| strategy | classifier | n_fits | total_seconds | mean_seconds_per_update | max_seconds | mean_train_rows |
|---|---|---|---|---|---|---|
| static | logreg | 1 | 2.6500 | 2.6500 | 2.6500 | 54000 |
| expanding | logreg | 5 | 54.3618 | 10.8724 | 14.1077 | 81000 |
| sliding | logreg | 5 | 31.3158 | 6.2632 | 8.9642 | 45000 |
| static | sgd | 1 | 5.0200 | 5.0200 | 5.0200 | 54000 |
| expanding | sgd | 5 | 61.5999 | 12.3200 | 17.1582 | 81000 |
| sliding | sgd | 5 | 40.2812 | 8.0562 | 9.6258 | 45000 |
| incremental | sgd | 5 | 7.3575 | 1.4715 | 7.1278 | 19200 |
| static | random_forest | 1 | 8.1800 | 8.1800 | 8.1800 | 54000 |
| expanding | random_forest | 5 | 100.5555 | 20.1111 | 26.4147 | 81000 |
