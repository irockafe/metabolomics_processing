import mwtab
import pandas as pd
import numpy as np

# scikit
from sklearn import preprocessing
from sklearn.cross_validation import StratifiedShuffleSplit
from sklearn.ensemble import RandomForestClassifier

import scipy.stats as stats

import matplotlib.pyplot as plt
import seaborn as sns

# My code
import data.mwtab_fxns as my_mwtab
import data.preprocessing as preproc
import project_fxns.rt_window_prediction as rtwin


local_path = '/home/irockafe/Dropbox (MIT)/Alm_Lab/projects/'
project_path = '/revo_healthcare/data/processed/ST000450/'
neg = '/ST000450_AN000706_negative_hilic.txt'
pos = '/ST000450_AN000705_positive_hilic.txt'

# Get positive mode metadata
mwtfile_gen = mwtab.read_files(local_path+project_path+pos)
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

# Preprocess feature table
# Replace NaNs
df = df.replace('\N', np.nan)
df = df.astype(float)

# Fill with half the min value
fill_val = df.min(axis=1).min() / 2
df_filled = df.fillna(value=fill_val)
df_pqn_filled = preproc.correct_dilution_factor(df_filled)

# Make sure no systematic bias in feature intensity between case/control
print "classes: {c}".format(c=metadata_df['Disease'].unique())
case_labels = metadata_df[metadata_df['Disease'] == 'CFS'].index
control_labels = metadata_df[metadata_df['Disease'] == 'Normal'].index


def mw_pval_dist(case, control):
    '''
    case - dataframe containing case
    control - dataframe with control samples
        All should have same features (columns)
    '''
    # get parametric pvals
    mann_whitney_vals = pd.DataFrame(np.full([case.shape[1], 2], np.nan),
                                     index=case.columns, columns=['u', 'pval'])
    for idx, case_vals in case.iteritems():
        control_vals = control[idx]
        u, pval = stats.mannwhitneyu(case_vals, control_vals)
        mann_whitney_vals.loc[idx, 'u'] = u
        mann_whitney_vals.loc[idx, 'pval'] = pval

    # plot mw pval distribution
    mann_whitney_vals.hist('pval')
    plt.title('mann-whitney pval between case and control - normal assumption')
    plt.show()

    # plot distribution of mean intensities
    case_mean = case.mean(axis=0)
    ctrl_mean = control.mean(axis=0)
    sns.distplot(np.log10(case_mean), label='case')
    sns.distplot(np.log10(ctrl_mean), label='control')
    plt.xlabel('log_10 intensity')
    plt.title('Mean intensity of case vs. control')
    plt.legend()
    plt.show()
    u, pval = stats.mannwhitneyu(case_mean, ctrl_mean)
    print 'pval (MannW) of intensities between case and control: ', pval

print "raw data, nan filled"
mw_pval_dist(df_filled.loc[case_labels], df_filled.loc[control_labels])

print "pqn-data nan filled"
mw_pval_dist(df_pqn_filled.loc[case_labels], df_pqn_filled.loc[control_labels])

# Make a classifier
random_state = 1
test_size = 0.3
n_iter = 50
n_trees = 1000
cross_val = StratifiedShuffleSplit(y, n_iter=n_iter, test_size=test_size,
                                   random_state=random_state)
clf = RandomForestClassifier(n_estimators=n_trees,
                             random_state=random_state)

results_path = '/revo_healthcare/results/ST000450/pos/'
roc_path = local_path + results_path + '/figures/roc_curve_rf.pdf'
auc_vals = rtwin.roc_curve_cv(df_pqn_filled.as_matrix(), y, clf, cross_val,
                              save=True, path=roc_path)
auc_val_path = local_path + results_path + '/data/auc_vals.npy'
np.save(auc_val_path, auc_vals)

#
