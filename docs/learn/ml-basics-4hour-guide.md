# Machine Learning - 4 Hour Learning Guide

## Error
```
#### Accuracy -> Not incase of imballance data, here only Presiciton, Recall, F1, ex 500 data by only 1 faude, banking app - faude transation, Passward reset, help SMOTE(synthatic data)
#### Presiciton (average="macro") -> how much model predected, and how many where acurate,  - 10 fraud, but actually 8 fraud => pression = 80%
#### Recall -> Acuatal model test on the Training data, unseen data(test date), accutally -10fraud, 10 result, 100% reacall, 8result then 80%
#### F1 -> Balance Between Precission and recall - number of fales positive and false -ve, how much is acurrate.SMOTE
Accuracy	Precision (macro)	Recall (macro)	F1 (macro)
```

## Hour 1: Foundations
- What is AI, ML, Deep Learning
- Supervised Learning
- Unsupervised Learning
- Reinforcement Learning
- Mean, Median, Mode
- Standard Deviation
- Vectors
- y = mx + b

## Hour 2: Data Preprocessing
- Missing Values
- dropna()
- fillna()
- Label Encoding
- One-Hot Encoding
- StandardScaler
- MinMaxScaler
- SMOTE -(only incase of imballance data) making large data like banking to faude test data, to do the all the above metrix - making better data like 50 data, 50 fraude data, making copy of the data.
- Train-Test Split

## Hour 3: Machine Learning Algorithms
### Regression
- Linear Regression

### Classification
- Logistic Regression
- KNN
- Decision Tree

### Model Fit
- Underfitting
- Good Fit
- Overfitting

## Hour 4: Model Evaluation
### Regression Metrics
- MAE
- MSE
- RMSE
- R²

### Classification Metrics
- Accuracy
- Precision
- Recall
- F1 Score
- Confusion Matrix

## Scikit-Learn Workflow

1. Collect Data
2. Understand Data
3. Handle Missing Values
4. Encode Data
5. Scale Features
6. Train-Test Split
7. Train Model
8. Predict
9. Evaluate
10. Improve
11. Deploy
