import numpy as np
import matplotlib.pyplot as plt
import mwtab
# scikit
from sklearn import preprocessing

# My code
import data.mwtab_fxns as my_mwtab


def prevalence_threshold(df, threshold=0.5):
    '''
    PURPOSE:
        Take a (samples x features) dataframe and return only
        features present in fraction of samples > the threshold
    INPUT:
        df - pandas dataframe (samples x features)
    OUTPUT:
        output - dataframe containing only the columns (features)
            that pass the prevlaence threshold
    '''

    print "Requiring sample to be present in %s percent of samples" % threshold
    test = ((df > 1e-20).sum(axis=0) / df.shape[0]) >= threshold
    output = df[df.columns[test]]
    return output


def correct_dilution_factor(X, plot=False):
    '''
    GOAL:
        Correct for systematically biased intensity values
        by finding a dilution factor (if the median of
        feature mean-intensities is high, your sample is too concentrated)
    INPUT:
        X - (samples x features) dataframe
        plot - whether or not to plot histogram of dilution factors
    OUTPUT:
        X_pqn - Dataframe (samples x features)
            normalized by dilution factor
    '''
    feature_means = np.mean(X, axis=0)
    # mean-center each feature
    X_mean_centered = np.divide(X, feature_means[np.newaxis, :])
    # ignore the nans when calculating median
    dilution_factors = np.nanmedian(X_mean_centered, axis=1)
    if plot:
        plt.hist(dilution_factors, bins=50)
        plt.title('Dilution factor distribution')
        plt.show()
    # broadcast correctly to divide column-wise
    X_pqn = np.divide(X, dilution_factors[:, np.newaxis])
    return X_pqn


def mwtab_to_feature_table(mwtab_path):
    '''
    GOAL:
       Given an mwtab file, get the feature table, class labels,
       and metadata from that file
    INPUT:
        mwtab_path - path to file
    OUTPUT:
        df: pandas dataframe (samples, features)
        y: class labels (encoded as numbers)
        metadata_df: pandas dataframe containing metadata from mwtab
            (samples x factors)
    '''
    # Get metadata
    mwtfile_gen = mwtab.read_files(mwtab_path)
    mwtfile = next(mwtfile_gen)
    metadata_df = my_mwtab.factors_to_df(mwtfile)
    df = my_mwtab.get_feature_table(mwtfile)
    assert(metadata_df.index == df.index).all()
    print 'df shape', df.shape
    print 'metadata shape', metadata_df.shape

    # convert classes to numbers
    le = preprocessing.LabelEncoder()
    le.fit(metadata_df['Disease'])
    y = le.transform(metadata_df['Disease'])

    return df, y, metadata_df


def standard_preprocessing(X):
    '''
    GOAL: Correct for dilution (pqn-normalize), impute missing
        values as 1/2 minimum, scale using median and IQR
    INPUT:
        Feature table (samples, features)
    OUTPUT:
        numpy matrix (samples, features) after dilution factor correction,
        missing value imputation, and scaling using median and IQR
    '''
    # TODO: Add this as part of a pipeline
    x_pqn = correct_dilution_factor(X)
    min_vals = x_pqn.min(axis=1).min() / 2
    x_pqn_filled_halfmin = x_pqn.fillna(value=min_vals)
    x_pqn_filled_halfmin_scaled = (preprocessing.RobustScaler()
                                   .fit_transform(x_pqn_filled_halfmin)
                                   )

    return x_pqn_filled_halfmin_scaled

#
