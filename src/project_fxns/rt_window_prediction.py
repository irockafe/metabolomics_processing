import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter

from sklearn.metrics import roc_curve, auc
from sklearn.ensemble import RandomForestClassifier
from sklearn.cross_validation import StratifiedShuffleSplit
from sklearn.utils import shuffle

from scipy import interp

import pickle

# My code
import visualization.viz as viz


def get_tpr_fpr(X, y, clf, cross_val):
    '''
    GOAL:
        Get the stats to plot an ROC curve
    INPUT:
        X - (samples x features) numpy array
        y - (samles,) numpy array
        clf - classifier to use
        cross_val - cross-validation strategy to use
    '''
    t1 = time.time()
    # collect vals for the ROC curves
    tpr_list = []
    mean_fpr = np.linspace(0, 1, 100)
    auc_list = []

    # Get the false-positive and true-positive rate
    for i, (train, test) in enumerate(cross_val):
        clf.fit(X[train], y[train])
        y_pred = clf.predict_proba(X[test])[:, 1]

        # get fpr, tpr
        fpr, tpr, thresholds = roc_curve(y[test], y_pred)
        roc_auc = auc(fpr, tpr)
        tpr_list.append(interp(mean_fpr, fpr, tpr))
        tpr_list[-1][0] = 0.0
        auc_list.append(roc_auc)

        if (i % 10 == 0):
            print('{perc}% done! {time}s elapsed'.format(
                 perc=100*float(i)/cross_val.n_iter, time=(time.time() - t1))
                 )
    return tpr_list, auc_list, mean_fpr


def roc_curve_cv(X, y, clf, cross_val, color='blue',
                 path='/home/irockafe/Desktop/roc.pdf',
                 save=False, plot=False,
                 ):
    '''
    PURPOSE:
        Creates an ROC curve
    INPUT:
        X - (samples x features) numpy array
        y - (samles,) numpy array
        clf - classifier to use
        cross_val - cross-validation strategy to use
        color - color to plot ROC curve
        path- where to dump a pdf of the cross-validated ROC curve
    '''
    tpr_list, auc_list, mean_fpr = get_tpr_fpr(X, y, clf, cross_val)
    # Return the stuff you can use to plot
    print 'Plottttt!'
    my_plt = viz.roc_curve(tpr_list, mean_fpr, auc_list,
                           cross_val, path, color=color)
    if plot:
        my_plt.show()

    return my_plt


def roc_curve_cv_null(X, y, clf, cross_val, num_shuffles=5, color='black',
                      path='/home/irockafe/Desktop.roc.pdf',
                      save=False, plot=True,
                      ):
    '''
    PURPOSE:
        Creates a null ROC curve by shuffling class labels
    INPUT:
        X - (samples x features) numpy array
        y - (samles,) numpy array
        clf - classifier to use (scikit)
        cross_val - cross-validation strategy to use (scikit crossvalidation
            object)
        num_shuffles - number of times to shuffle class labels
        color - color to plot the ROC curve
        path- where to dump a pdf of the cross-validated ROC curve
    '''
    tpr_list, auc_list, mean_fpr = get_tpr_fpr(X, y, clf, cross_val)
    # Return the stuff you can use to plot
    # shuffle y lots of times
    # collect tpr and fpr rates from each fold and shuffle
    # Then plot the mean of them all
    null_tpr_list = []
    null_auc_list = []
    for i in range(0, num_shuffles):
        # Iterate through the shuffled y vals and repeat with appropriate params
        # Retain the auc vals for final plotting of distribution
        y_shuffle = shuffle(y)
        cross_val.y = y_shuffle
        cross_val.y_indices = y_shuffle
        print ('Number of differences b/t original and' +
               'shuffle: {num}'.format(num=(y == cross_val.y).sum())
               )
        # Get auc values for number of iterations
        mean_tpr_null, auc_list_null, mean_fpr_null = get_tpr_fpr(X,
                                                                  y_shuffle,
                                                                  clf,
                                                                  cross_val)
        null_tpr_list += mean_tpr_null
        null_auc_list += auc_list_null

    my_plt = viz.roc_curve(null_tpr_list, mean_fpr_null, null_auc_list,
                           cross_val, path, color=color)
    if save:
        my_plt.savefig(path, format='pdf')
    if plot:
        my_plt.show()
    return my_plt


def rt_slice(df, rt_bounds):
    '''
    PURPOSE:
        Given dataframe (features x samples)
        with 'mz' and 'rt' column headers,
        retain only the features whose rt is between left
        and right bounds (1st and second entries of rt_bounds)
    INPUT:
        df - a pandas dataframe feature table with 'mz' and 'rt' column
            headers (i.e. from xcms), along with sample column headers
            and features along the rows
        rt_bounds: the boundaries of your rt_slice (left_bound, right_bound)
    OUTPUT:
        Feature table containing only the features between the specified.
        rt window. Note that it also contains the rt and mz columns, too.
    '''

    out_df = df.loc[(df['rt'] > rt_bounds[0]) &
                    (df['rt'] < rt_bounds[1])]
    return out_df


def plot_mz_rt(df, rt_bounds, path='/home/irockafe/Desktop/poop.pdf',
               bins=100):
    '''
    PURPOSE: Plot the mz/rt space of your dataset,
        along with histograms of the rt and mz presence
    INPUT:
        df - a pandas dataframe feature table,
            containing columns labeled 'rt' and 'mz', along with
            the sample columns
        rt_bounds - iterable containing retention time bounds
            for a particular slice: (left bound, right bound)
        path - where to save the figure to.
    OUTPUT:
        a pdf file showing mz/rt points and the rt-bound

    '''

    # the random data
    x = df['rt']
    y = df['mz']
    print np.max(x)
    print np.max(y)
    nullfmt = NullFormatter()         # no labels

    # definitions for the axes
    left, width = 0.1, 0.65
    bottom, height = 0.1, 0.65
    bottom_h = left_h = left + width + 0.02

    rect_scatter = [left, bottom, width, height]
    rect_histx = [left, bottom_h, width, 0.2]
    rect_histy = [left_h, bottom, 0.2, height]

    # start with a rectangular Figure
    plt.figure(1, figsize=(10, 10))

    axScatter = plt.axes(rect_scatter)
    axHistx = plt.axes(rect_histx)
    axHisty = plt.axes(rect_histy)

    # no labels
    axHistx.xaxis.set_major_formatter(nullfmt)
    axHisty.yaxis.set_major_formatter(nullfmt)

    # the scatter plot:
    axScatter.scatter(x, y, s=1)
    x_min = np.min(x)-50
    x_max = np.max(x)+50
    axScatter.set_xlim(x_min, x_max)
    y_min = np.min(y)-50
    y_max = np.max(y)+50
    axScatter.set_ylim(y_min, y_max)

    # Add vertical/horizontal lines to scatter and histograms
    axScatter.axvline(x=rt_bounds[0], lw=2, color='r', alpha=0.5)
    axScatter.axvline(x=rt_bounds[1], lw=2, color='r', alpha=0.5)

    axHistx.axvline(x=rt_bounds[0], lw=2, color='r', alpha=0.5)
    axHistx.axvline(x=rt_bounds[1], lw=2, color='r', alpha=0.5)

    axHistx.hist(x.dropna(), bins=bins)
    axHisty.hist(y.dropna(), bins=bins, orientation='horizontal')

    axHistx.set_xlim(axScatter.get_xlim())
    axHisty.set_ylim(axScatter.get_ylim())

    axScatter.set_ylabel('m/z', fontsize=30)
    axScatter.set_xlabel('Retention Time', fontsize=30)

    axHistx.set_ylabel('# of Features', fontsize=20)
    axHisty.set_xlabel('# of Features', fontsize=20)

    plt.savefig(path,
                format='pdf')
    plt.show()


def slice_and_predict(df, y, rt_window, not_samples, rf_estimators=1000,
                      n_iter=10, test_size=0.3, random_state=1,
                      mzrt_path='/home/irockafe/Desktop/poop.pdf',
                      roc_path='/home/irockafe/Desktop/roc.pdf',
                      ):
    '''
    PURPOSE:
    INPUT:
        df -
            pandas dataframe, from xcms, that includes columns with 'mz'
            and 'rt'. Do all your preprocessing before this function!
            (sample-thresholds, normalization, etc)
        y -
            class-labels encoded by scikit LabelEncoder.
            Make sure their order matches the dataframe's
        rt_window -
            (left_bound, right_bound) of retention times
        not_samples -
            a list of column headers to be removed from df before
            converting to feature table e.g. ['mz', 'rt', 'mzmin']
        rf_estimators -
            Number of trees in random forest
        n_iter -
            Number of cross-validation iterations
        test_size -
            fraction of samples to be held back as test set
        random_state -
            numpy random state
        mzrt_path -
            where file showing mzrt files will be saved
        roc_path -
            where file showing roc curve will be saved
    OUTPUT:
        pdf files
            - showing mzrt space, with histograms of density
            - showing cross-validated ROC curves
        auc_vals -
            The auc values from cross-validation (this way you can plot
            stuff)
    '''

    # plot selection
    plot_mz_rt(df, rt_window, path=mzrt_path)
    # Get slice and convert to feature table
    df_slice = rt_slice(df, rt_window)
    # remove columns with adduct info, extranneous stuff: mz, rt, etc
    samples_list = df_slice.columns.difference(not_samples)
    # convert to samples x features
    df_slice_processed = df_slice[samples_list].T
    X_slice = df_slice_processed.as_matrix()
    print "slice shape", X_slice.shape
    print 'y shape', y.shape

    # Run RF
    rf_estimators = rf_estimators
    n_iter = n_iter
    test_size = test_size
    random_state = random_state
    cross_val_rf = StratifiedShuffleSplit(y, n_iter=n_iter, test_size=test_size,
                                          random_state=random_state)
    clf_rf = RandomForestClassifier(n_estimators=rf_estimators,
                                    random_state=random_state)
    tpr_vals, auc_vals, mean_fpr = roc_curve_cv(X_slice, y, clf_rf,
                                                cross_val_rf,
                                                save=True, path=roc_path)
    return auc_vals


def make_sliding_window(min_val, max_val, width, step):
    '''
    PURPOSE: Create a sliding window given min, max, window width
        and step-size
    INPUT:
        min_val: Minimum value
        max_val: Maximum value
        width: Window width
        step: stepsize for each window
    OUTPUT:
        list of tuples [(left,right),(left2, right2),...]
        that give the bounds of a sliding window
    '''
    if step > width:
        raise ValueError("Your step should be less than" +
                         "or equal to the width of the window")
    left_bound = np.arange(min_val, max_val, step)
    right_bound = left_bound + width
    rt_bounds = zip(left_bound, right_bound)
    # remove any bounds that go past the maximum value
    for idx, i in enumerate(rt_bounds):
        if i[1] > max_val:
            rt_bounds.pop(idx)
    return rt_bounds


def sliding_rt_window_aucs(X_df, y, sliding_window, not_samples,
                           rf_trees=500, n_iter=3, test_size=0.3,
                           output_path='/home/irockafe/Desktop/'):

    all_aucs = np.full([len(sliding_window), n_iter], np.nan)
    for i, rt_slice in enumerate(sliding_window):
        print 'RT plot', rt_slice
        auc_vals = slice_and_predict(X_df, y, rt_slice,
                                     not_samples, rf_estimators=rf_trees,
                                     n_iter=n_iter, test_size=test_size,
                                     random_state=1,
                                     mzrt_path=(output_path +
                                                '/mzrt_window_%i.pdf' % i),
                                     roc_path=(output_path +
                                               'roc_window_%i.pdf' % i))
        # add aucs vals to array
        all_aucs[i] = auc_vals
        print '\n\n\n'+'-'*50+'NEXT ROUND'+'-'*50+'\n\n\n'
        # write aucs to file

    pickle.dump(all_aucs,
                open(output_path+'auc_vals.pkl', 'wb'))
    return all_aucs


def plot_auc_vs_rt(auc_vals, sliding_window, df,
                   path, plot=True, save=True):
    # plot auc_vals vs. median of sliding_window
    # get middle of sliding window points
    x = [np.mean(i) for i in sliding_window]
    y_mean = [np.mean(i) for i in auc_vals]
    y_std = [np.std(i) for i in auc_vals]

    # Set up the figure
    left, width = 0.1, 0.65
    bottom, height = 0.1, 0.65
    bottom_h = left + width + 0.02

    rect_scatter = [left, bottom, width, height]
    rect_histx = [left, bottom_h, width, 0.2]

    # Start with rect figure
    plt.figure(1, figsize=(10, 10))
    axScatter = plt.axes(rect_scatter)
    axHistx = plt.axes(rect_histx)
    # no labels
    nullfmt = NullFormatter()
    axHistx.xaxis.set_major_formatter(nullfmt)
    # scatter plot
    axScatter.scatter(x, y_mean, 100)
    axScatter.errorbar(x, y_mean, yerr=y_std,
                       fmt='o', capsize=5)

    # Histograms
    axHistx.hist(df['rt'], bins=100)

    # Labels
    axScatter.set_ylabel('AUC', fontsize=30)
    axScatter.set_xlabel('Retention Time', fontsize=30)
    axScatter.set_ylim([0.5, 1.0])

    axHistx.set_ylabel('# of Features', fontsize=20)
    # plot a histogram of the feature prevalence
    plt.savefig(path, format='pdf')
    plt.show()

#
