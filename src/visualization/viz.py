import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import auc


def roc_curve(tpr_list, mean_fpr, auc_list,
              cross_val, path, color='blue', save=False):
    # get mean tpr and fpr
    mean_tpr = np.mean(tpr_list, axis=0)
    # make sure it ends up at 1.0
    mean_tpr[-1] = 1.0
    mean_auc = auc(mean_fpr, mean_tpr)
    std_auc = np.std(auc_list)

    # plot mean auc
    plt.plot(mean_fpr, mean_tpr,
             label='Mean AUC = %0.2f $\pm$ %0.2f' % (mean_auc,
                                                     std_auc),
             lw=3, color=color)

    # plot luck-line
    plt.plot([0, 1], [0, 1], linestyle='--', lw=1, color='r',
             alpha=0.5)

    # plot 1-std
    std_tpr = np.std(tpr_list, axis=0)
    tprs_upper = np.minimum(mean_tpr + std_tpr, 1)
    tprs_lower = np.maximum(mean_tpr - std_tpr, 0)
    plt.fill_between(mean_fpr, tprs_lower, tprs_upper, color=color,
                     alpha=0.2)

    plt.xlim([-0.05, 1.05])
    plt.ylim([-0.05, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC curve, {iters}'.format(iters=cross_val.n_iter) +
              ' iterations of {cv} cross validation'.format(
                cv='{train}:{test}'.format(test=cross_val.test_size,
                                           train=(1-cross_val.test_size))
                                                           )
              )
    plt.legend(loc="lower right")

    if save:
        plt.savefig(path,  format='pdf')
    return plt


#
