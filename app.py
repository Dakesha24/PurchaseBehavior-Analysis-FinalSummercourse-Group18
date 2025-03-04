from flask import Flask, render_template, request
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import plotly.graph_objs as go
import plotly.express as px
import plotly.io as pio
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

app = Flask(__name__)

# Load the dataset
file_path = 'dataset.csv'
data = pd.read_csv(file_path)

# Data preprocessing
X = data.drop('PurchaseStatus', axis=1)
y = data['PurchaseStatus']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the Random Forest model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Make predictions
y_pred = model.predict(X_test)

#accuracy number
number = accuracy_score(y_test, y_pred)
accuracy = "{:.3f}%".format(number * 100)

# Feature Importance
feature_importance = model.feature_importances_
features = X.columns

# Visualization for actual vs predicted purchase amounts
actual_vs_predicted = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred})
x_values = np.arange(len(actual_vs_predicted))  # Use indices as x values
y_actual = actual_vs_predicted['Actual']
y_predicted = actual_vs_predicted['Predicted']
# Calculate the coefficients for the linear regression line
m, b = np.polyfit(x_values, y_actual, 1)  # 1 indicates linear fit
# Create the regression line values
regression_line = m * x_values + b
# Create the figure
actual_vs_predicted_fig = go.Figure()
actual_vs_predicted_fig.add_trace(go.Scatter(x=x_values, y=y_actual, mode='markers', name='Actual', marker=dict(color='blue')))
actual_vs_predicted_fig.add_trace(go.Scatter(x=x_values, y=y_predicted, mode='markers', name='Predicted', marker=dict(color='orange')))
actual_vs_predicted_fig.add_trace(go.Scatter(x=x_values, y=regression_line, mode='lines', name='Regression Line', line=dict(color='red', dash='dash')))
actual_vs_predicted_fig.update_layout(
    xaxis_title='Index',
    yaxis_title='Purchase Amount',
    autosize=True,
    width=1000,
    height=500
)
actual_vs_predicted_graph = pio.to_html(actual_vs_predicted_fig, full_html=False)


def get_classification_report(y_test, y_pred):
    #Generate and save the classification report
    report = classification_report(y_test, y_pred, output_dict=True)
    report_df = pd.DataFrame(report).transpose()
    plt.figure(figsize=(10, 5))
    sns.heatmap(report_df.iloc[:-1, :].T, annot=True, cmap='Blues', fmt='.2f')
    plt.title('Classification Report')
    plt.xlabel('Metrics')
    plt.ylabel('Classes')
    plot_path = 'static/classification_report.png'
    plt.savefig(plot_path)
    plt.close()
    return plot_path


def plot_confusion_matrix(y_test, y_pred):
    #Plot and save the confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Class 0', 'Class 1'], yticklabels=['Class 0', 'Class 1'])
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Confusion Matrix')
    plot_path = 'static/confusion_matrix.png'
    plt.savefig(plot_path)
    plt.close()
    return plot_path


@app.route('/')
def index():
    # Visualization 1: Age Range Line Graph
    age_bins = [0, 18, 25, 35, 45, 55, 65, 100]
    age_labels = ['<18', '18-24', '25-34', '35-44', '45-54', '55-64', '65+']
    data['AgeRange'] = pd.cut(data['Age'], bins=age_bins, labels=age_labels, right=False)
    age_range_counts = data['AgeRange'].value_counts().sort_index()
    age_range_line = go.Scatter(x=age_range_counts.index, y=age_range_counts.values, mode='lines+markers')
    age_range_layout = go.Layout(xaxis=dict(title='Age Range'), yaxis=dict(title='Number of Purchases'))
    age_range_fig = go.Figure(data=[age_range_line], layout=age_range_layout)
    age_range_graph = pio.to_html(age_range_fig, full_html=False)
    
    # Visualization 2: Distribution of Purchases by Product Category
    category_pie = px.pie(data, 
                           names='ProductCategory', 
                           values='NumberOfPurchases', 
                           labels={'ProductCategory': 'Product Category'})
    # Update layout to customize size
    category_pie.update_layout(width=400, height=400)
    category_graph = pio.to_html(category_pie, full_html=False)
    
    # Visualization 3: Feature Importance
    feature_bar = go.Bar(x=features, y=feature_importance)
    feature_layout = go.Layout(xaxis=dict(title='Features'), yaxis=dict(title='Importance'))
    feature_fig = go.Figure(data=[feature_bar], layout=feature_layout)
    feature_graph = pio.to_html(feature_fig, full_html=False) 
    
    # Visualization 4: Distribution of Time Spent on Website
    time_spent_bar = px.bar(data, x='ProductCategory', y='TimeSpentOnWebsite', 
                            labels={'TimeSpentOnWebsite': 'Time Spent on Website (minutes)', 'ProductCategory': 'Product Category'}, 
                            color='ProductCategory', barmode='stack')
    time_spent_graph = pio.to_html(time_spent_bar, full_html=False)

    # Visualization 5: Distribution of Annual Income
    average_income = data.groupby('Age')['AnnualIncome'].mean().reset_index()

    compound_fig = go.Figure()
    compound_fig.add_trace(go.Scatter(
        x=average_income['Age'],
        y=average_income['AnnualIncome'],
        mode='lines+markers',
        name='Average Annual Income',
        line=dict(shape='spline')  # Smooth line
    ))
    
    compound_fig.update_layout(
        xaxis_title='Age',
        yaxis_title='Average Annual Income',
        width=600, height=400
    )
    income_graph = pio.to_html(compound_fig, full_html=False)
    
    
    return render_template('index.html', 
                           age_range_graph=age_range_graph, 
                           category_graph=category_graph,
                           feature_graph=feature_graph,
                           time_spent_graph=time_spent_graph,
                           income_graph=income_graph,
                           accuracy=accuracy)

@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/performance')
def performance():
    # Generate plots
    classification_report_path = get_classification_report(y_test, y_pred)
    confusion_matrix_path = plot_confusion_matrix(y_test, y_pred)
    
    return render_template('model.html', output=accuracy, actual_vs_predicted_graph=actual_vs_predicted_graph, classification_report_url=classification_report_path, confusion_matrix_url=confusion_matrix_path)

if __name__ == '__main__':
    app.run(debug=True)
