| strategy | classifier | n_fits | total_seconds | mean_seconds_per_update | max_seconds | mean_train_rows | update_rows |
|---|---|---|---|---|---|---|---|
| static | logreg | 1 | 2.8800 | 2.8800 | 2.8800 | 54000 |  |
| expanding | logreg | 5 | 59.1958 | 11.8392 | 16.9077 | 81000 |  |
| sliding | logreg | 5 | 25.9828 | 5.1966 | 7.8454 | 45000 |  |
| static | sgd | 1 | 3.9300 | 3.9300 | 3.9300 | 54000 |  |
| expanding | sgd | 5 | 52.0247 | 10.4049 | 14.6894 | 81000 |  |
| sliding | sgd | 5 | 31.8069 | 6.3614 | 7.6232 | 45000 |  |
| incremental | sgd | 5 | 5.9399 | 1.1880 | 5.7507 | 54000 | 10500 |
| static | random_forest | 1 | 8.1600 | 8.1600 | 8.1600 | 54000 |  |
| expanding | random_forest | 5 | 82.2242 | 16.4448 | 21.4566 | 81000 |  |

Notes: static seconds are the Step 4 model fit and exclude preprocessing; expanding, sliding and the incremental initial fit include the preprocessing fit. mean_train_rows is the rows of a full fit (incremental: the initial fit); update_rows is the mean rows of one incremental partial_fit.
