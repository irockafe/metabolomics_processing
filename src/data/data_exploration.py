import numpy as np
import pandas as pd
import seaborn as sns
import os
import matplotlib.pyplot as plt
# Code to explore raw data
# and get a feel for it


def plot_feature_sparsity(data, class_dict=None, fxn=None,  **kwargs):
    # data is in (samples x features)
    # sum all nans in each sample (true zeros)
    # divide by num_samples
    # class_dict - splits feature table
    # Assume anything lower than 1e-15 is floating-point zero
    sparsity = (data < 1e-15).sum(axis=1) / data.shape[1]
    axes = distplot_classes(sparsity, class_dict, fxn=fxn, **kwargs)
    return axes


def distplot_classes(data, class_dict=None, plt_fxn=sns.distplot,
                     fxn=None, **kwargs):
    # plot feautre distribution - could be mean intensity by passing mean
    # stdev by passing
    # **kwargs for the distplot command
    if class_dict:
        legend_entries = []
        axes = []
        for k, v in class_dict.iteritems():
            print(k)
            legend_entries.append(k)
            ax = distplot_classes(data.loc[v],
                                  plt_fxn=plt_fxn,
                                  fxn=fxn, **kwargs)
            axes.append(ax)
        ax.legend(legend_entries, loc='best')#$bbox_to_anchor=(1.2, 0.9))
        return axes
    # take the mean, std, etc of data
    # or don't
    if fxn:
        ax = plt_fxn(fxn(data), **kwargs)
        return ax
    elif not fxn:
        ax = plt_fxn(data, **kwargs)
        return ax


def two_group_stat(data, class_dict, fxn, **kwargs):
    # run any-ish two group stat-test
    # that looks like fxn(x,y)
    # I'm using mann-whitney
    # class dict: {class_label: [sample_names]}
    # data: (sample x feature)
    keys = [k for k in class_dict.keys()]
    stat = data.apply(
                (lambda col: (
                    fxn(
                        col.loc[class_dict[keys[0]]],
                        col.loc[class_dict[keys[1]]],
                        **kwargs)
                    )
                ),
                axis=0)
    return stat


def fill_zero_nan(data,
        zero_fill=None):
    # fill zeros and nans in a dataframe
    # default is to fill each sample with 1/2 the minimum intensity
    # detected
    if not zero_fill:
        zero_fill = data[data > 1e-15].min(axis=1).min() / 2
    return (data[data > 1e-15].fillna(zero_fill))


def tidy(data):
    # Assumes (samples x features)
    tidy_data = (data.reset_index()
                      .melt(id_vars='index',
                          ))
    return tidy_data


def plot_categorical_split(tidy_data, sample_names,
        axes, step, class_name=None, plot_type=sns.boxplot,
        ylabel='y', xlabel='x',
        **kwargs):
    # helper fxn
    # split up plotting lots of categorical things
    # i.e. violin plots boxplots, etcss
    groups = [sample_names[i:i+step]
        for i in xrange(0,len(sample_names), step)]
    for grp in groups:
        ax = plot_type(x='index', y='value',
            data=tidy_data, order=grp)
        ax.set_ylabel(ylabel)
        ax.set_xlabel(xlabel)
        if class_name:
            ax.set_title('Class: %s' % class_name)
        axes.append(ax)
        plt.show()
    return axes


def save_axes(axes_list, base_path,
        file_names, ftype='pdf'):
    # if you've got an iterable
    if type(file_names) != 'str':
        for i, ax in enumerate(axes_list):
            filepath = os.path.join(base_path,
                    file_names[i] + '.%s' % ftype)
            ax.figure.savefig(filepath)
    else:
        for i, ax in enumerate(axes_list):
            filepath = os.path.join(base_path,
                    file_names+('_%s.%s' % (i, ftype))
                    )
            ax.figure.savefig(filepath)


def sample_feature_intensity(tidy_data,
        class_dict=None, step=10, plot_type=sns.boxplot,
        ylabel='', xlabel='',
        **kwargs):
    # plot a max of {step} violin plots per plot
    # separate by class labels if a dict given
    # class_dict: {'malaria': [100_P, 101_P], 'healthy': [200_P, 201_P]}
    axes = []
    if class_dict:
        for k, v in class_dict.iteritems():
            axes = plot_categorical_split(tidy_data,
                    v, axes, step, class_name=k,
                    plot_type=plot_type,
                    ylabel=ylabel, xlabel=xlabel,
                    **kwargs)
    else:
        sample_names = tidy_data['index'].unique()
        axes = plot_categorical_split(tidy_data,
                sample_names, axes, step,
                plot_type=plot_type,
                ylabel=ylabel, xlabel=xlabel,
                **kwargs)
    return axes


def plot_pvals_stratified(covar, stats,
        covar_name='Covariate', ngroups=6, n_cols=3,
        title_fxn=np.log10, **kwargs):
    # covar series, index is features142G
    # stats - pd.Series of statistics indexed by feature
    #     covar and stats must have same index
    # ngroups - number of groups to split it into
    # TODO bug when plotting a single row of plots
    #   currently just ignore it
    groups = np.array_split(covar.sort_values(), ngroups)
    n_cols=3.0
    n_rows = np.ceil(ngroups/n_cols)
    fig, axes = plt.subplots(int(n_rows), int(n_cols),
            sharex=True, sharey=True)
    fig.suptitle(covar_name)
    for i, grp in enumerate(groups):
        strat_stat = stats[grp.index]
        row=  np.floor(i/n_cols)
        col = i%n_cols  # remainder
        try:
            ax = sns.distplot(strat_stat, kde=False,
                    ax=axes[int(row), int(col)], **kwargs)
        except:
            print(('A bug I havent fixed means that'
                ' you must give ngroups > n_cols. Currently'
                ' ngroups=%s n_cols=%s' % (ngroups, n_cols)))
            raise
        # Default is to show the log_10 differences
        # if specified
        if title_fxn:
            ax.set_title('{strat}: {mini:.1f}:{maxi:.1f}'.format(
                strat=i, mini=title_fxn(grp.min()), maxi=title_fxn(grp.max())
                )
            )
        elif title_fxn == None:
            ax.set_title('{strat}: {mini:.1f}:{maxi:.1f}'.format(
                strat=i, mini=grp.min(), maxi=grp.max()
                )
            )


        # first plot, add ylabel
        if i == 0:
            ax.set_ylabel('Count')
        # bottom row of plots, add xlabel
        if i == (n_rows*n_cols - n_cols):
            ax.set_xlabel('pval')
    return axes


