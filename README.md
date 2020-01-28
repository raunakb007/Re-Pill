# Re-Pill READ ME

When you are prescribed medication by a Doctor, it is crucial that you complete the dosage cycle in order to ensure that you recover fully and quickly. Unfortunately forgetting to take your medication is something that we have all done. Failing to run the full course of medicine often results in a delayed recovery and leads to more suffering through the painful and annoying symptoms of illness. This has inspired us to create Re-Pill. With Re-Pill, you can automatically generate scheduling and reminders to take you medicine by simply uploading a photo of your prescription.

# What it does

A user uploads an image of their prescription which is then processed by image to text algorithms that extract the details of the medication. Data such as the name of the medication, its dosage, and total tablets is stored and presented to the user. The application synchronizes with google calendar and automatically sets reminders for taking pills into the user's schedule based on the dosage instructions on the prescription. The user can view their medication details at any time by logging into Re-Pill.

# How to Set Up

Install The libraries found in the requirements.txt file.

We use Google Cloud Firestore to handle our data. Here is a link to get set up on Firestore:

https://firebase.google.com/docs/firestore/quickstart

We also are utilizing Google-Calendar API. A quick guide can be found here:

https://developers.google.com/calendar/quickstart/python

To run the app, run "python3 main.py" in the root directory.
