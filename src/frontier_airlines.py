import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
import scipy.stats as scs

plt.rcParams['font.size'] = 13
plt.rcParams['axes.labelsize'] = 'large'
plt.rcParams['xtick.labelsize'] = 'large'
plt.rcParams['ytick.labelsize'] = 'large'
plt.rcParams['lines.linewidth'] = 2

def time_of_day(ts):
    '''
    Parameters
        ts: Takes in a timestamp
    Returns
        String of different time buckets in 24 hour format
    '''
    if ts<= 4:
        return '01 to 04'
    elif ts<=8:
        return '05 to 08'
    elif ts<=12:
        return '09 to 12'
    elif ts<=16:
         return '13 to 16'
    elif ts<=20:
        return '17 to 20'
    elif ts<=24:
        return '21 to 24'
    else:
        return np.nan

def clean_df(file_path):
    '''
    Parameters
        file_path: path to csv file as string
    Returns
        Cleaned dataframe
    '''
    unclean_df = pd.read_csv(file_path,header=1,usecols=['FlightDate','BookingDate','SegmentOrigin','SegmentDest',
        'FareClass','BookingAgent'])
    unclean_df.drop(unclean_df.index[0],inplace=True)
    unclean_df['Origin-Dest'] = unclean_df['SegmentOrigin']+'-'+unclean_df['SegmentDest']
    unclean_df.drop(['SegmentOrigin','SegmentDest'],axis=1,inplace=True)
    unclean_df['FlightDate']=pd.to_datetime(unclean_df['FlightDate'])
    unclean_df.replace(r'^\s*$', np.nan, regex=True,inplace=True)
    unclean_df['BookingDate']=pd.to_datetime(unclean_df['BookingDate'],errors='coerce')
    unclean_df['BookingTimeOfDay'] = unclean_df['BookingDate'].dt.hour.apply(time_of_day)
    unclean_df['RevenueLag(days)'] = (unclean_df['FlightDate']-unclean_df['BookingDate']).dt.days
    unclean_df.dropna(inplace=True,axis=0)
    unclean_df['BookingDate']=unclean_df['BookingDate'].dt.date
    nonrev_standby= unclean_df[unclean_df['FareClass']=='AS'].index
    nonrev_positive= unclean_df[unclean_df['FareClass']=='AP'].index
    unclean_df.drop(nonrev_positive, inplace = True)
    unclean_df.drop(nonrev_standby, inplace = True)
    return unclean_df

def chi_square(df,exp):
    '''
    Parameters
        df: grouped data frame
        exp: expected value
    Returns
        Chi-square and accompanying P-Value
    '''
    expected_lst=[exp]*len(df)
    return scs.chisquare(df['RevenueLag(days)'],f_exp=expected_lst)

if __name__ == '__main__':
    path ="../../../Downloads/SkyLedgerReconciliationExtract_FrontierAirlines_URExtract.csv"
    frontier_df = clean_df(path)

    #plot showing revenue lag versus booking hour
    booked_at = frontier_df.groupby('BookingTimeOfDay').mean().reset_index()
    fig, ax = plt.subplots(figsize=(14,7))
    ax.bar(booked_at['BookingTimeOfDay'],booked_at['RevenueLag(days)'],color='green',zorder=1)
    ax.set_xlabel('Time Of Day (24 Hour)', fontsize=14)
    ax.set_ylabel('Days', fontsize=14)
    ax.set_title('Revenue Lag Grouped by Purchase Hour')
    ax.hlines(frontier_df['RevenueLag(days)'].mean(),0,5,zorder=2,label='Mean of Data Set',linestyle='--')
    ax.legend()
    plt.tight_layout()
    ax.set_facecolor('lightgrey')
    ax.set_yticks(np.arange(0,51,5))
    plt.savefig('../images/LagVsHour.png',dpi=500)

    #plot showing revenue lag versus different fare class
    fare_class= frontier_df.groupby('FareClass').mean().reset_index().sort_values('RevenueLag(days)',ascending=True)
    fig, ax = plt.subplots(figsize=(14,7))
    ax.bar(fare_class['FareClass'],fare_class['RevenueLag(days)'],color='green',zorder=1)
    ax.set_xlabel('Fare Class', fontsize=14)
    ax.set_ylabel('Days', fontsize=14)
    ax.set_yticks(np.arange(0,121,10))
    ax.set_title('Revenue Lag Grouped by Fare Class')
    ax.hlines(frontier_df['RevenueLag(days)'].mean(),'Z','N',zorder=2,label='Mean of Data Set',linestyle='--')
    ax.legend()
    plt.tight_layout()
    ax.set_facecolor('lightgrey')
    plt.savefig('../images/LagVsFareClass.png',dpi=500)

    #plot showing revenue lag versus different fare class without class N
    fig, ax = plt.subplots(figsize=(14,7))
    ax.bar(fare_class['FareClass'].head(19),fare_class['RevenueLag(days)'].head(19),color='green',zorder=1)
    ax.set_xlabel('Fare Class', fontsize=14)
    ax.set_ylabel('Days', fontsize=14)
    ax.set_yticks(np.arange(0,121,10))
    ax.set_title('Revenue Lag Grouped by Fare Class')
    ax.hlines(frontier_df['RevenueLag(days)'].mean(),'Z','I',zorder=2,label='Mean of Data Set',linestyle='--')
    ax.legend()
    plt.tight_layout()
    ax.set_facecolor('lightgrey')
    plt.savefig('../images/LagVsFareClassWithoutN.png',dpi=500)

    #origin and destination combinations with more than 100 bookings
    origin_dest_df= frontier_df[frontier_df.groupby('Origin-Dest')['Origin-Dest'].transform('size')>100]
    origin_dest_top= origin_dest_df.groupby('Origin-Dest').mean().reset_index().sort_values('RevenueLag(days)',ascending=True).head(20)
    origin_dest_bottom= origin_dest_df.groupby('Origin-Dest').mean().reset_index().sort_values('RevenueLag(days)',ascending=True).tail(20)

    #plot showing origin destination combinations with 20 longest revenue lags
    fig, ax = plt.subplots(figsize=(14,7))
    ax.bar(origin_dest_bottom['Origin-Dest'],origin_dest_bottom['RevenueLag(days)'],color='green',zorder=1)
    ax.set_xlabel('Origin-Dest', fontsize=14)
    ax.set_ylabel('Days', fontsize=14)
    ax.hlines(frontier_df['RevenueLag(days)'].mean(),0,19,zorder=2,label='Mean of Data Set',linestyle='--')
    ax.legend()
    plt.xticks(rotation=32, fontsize=12, ha='right')
    ax.set_title('Revenue Lag Grouped by Origin Destination (Longest 20)')
    ax.set_facecolor('lightgrey')
    plt.tight_layout()
    plt.savefig('../images/LagVsOrgDestB.png',dpi=500)

    #plot showing origin destination combinations with 20 shortest revenue lags
    fig, ax = plt.subplots(figsize=(14,7))
    ax.bar(origin_dest_top['Origin-Dest'],origin_dest_top['RevenueLag(days)'],color='green',zorder=1)
    ax.set_xlabel('Origin-Dest', fontsize=14)
    ax.set_ylabel('Days', fontsize=14)
    ax.hlines(frontier_df['RevenueLag(days)'].mean(),0,19,zorder=2,label='Mean of Data Set',linestyle='--')
    ax.legend()
    ax.set_yticks(np.arange(0,51,5))
    plt.xticks(rotation=32, fontsize=12, ha='right')
    ax.set_title('Revenue Lag Grouped by Origin Destination (Shortest 20)')
    plt.tight_layout()
    ax.set_facecolor('lightgrey')
    plt.savefig('../images/LagVsOrgDestT.png',dpi=500)

    #setting df for all origin and destination combos
    origin_dest= origin_dest_df.groupby('Origin-Dest').mean().reset_index().sort_values('RevenueLag(days)',ascending=True)

    #Chi-square and P value for all graphs
    booked_chi,booked_p = chi_square(booked_at,frontier_df['RevenueLag(days)'].mean())
    fare_chi,fare_p = chi_square(fare_class,frontier_df['RevenueLag(days)'].mean())
    origin_chi,origin_p = chi_square(origin_dest,frontier_df['RevenueLag(days)'].mean())


