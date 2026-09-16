Team 8 : Kshent, Zhi Yueh, HuiFen, Finn, Hasini
Github link : https://github.com/Kshent/inf1103-team8-project.git

1.Problem Statement and Target Users
1.1 Problem Statement 
Booking a hotel is often a time consuming process . People struggle to find places that match all their specific needs, such as group size, budget limits, room features and transport links. Furthermore, travellers have to do extra research to find nearby places to dine and visit once they decide on a hotel. 

This proposal discusses a project that solves these issues by creating an AI hotel recommendation app. Users will simply type in their requests in plain language and the app instantly finds the top 3 best matching hotels while suggesting nearby food and activities for each option. More specifically, we plan to solve these issues through reduced search time, simplification of hotel filtering process (no need for manual selection of checkboxes, radio buttons etc), support for specific preferences (halal prayer room/amenities they need), curated recommendations of hotels, food and places of interest recommendations as well as ease of access to information (data generated gets sent to user email).

1.2 Target Users
The application is designed for all types of travellers : solo travellers, families and groups, business travellers, staycation seekers looking for suitable hotels based on their budget.

2. User inputs
Location (Mandatory): Users are required to provide their intended travel destination, such as Busan, South Korea.

Price Range (Mandatory): Users are required to specify their preferred hotel price range in SGD using a range slider, for example, SGD 300–500.

Email Address (Mandatory): Users will need to provide a valid email address, so that hotel recommendations can be sent. Email of the user and recommended content sent to the email will be stored in the system database.

Additional Preferences (Optional): Users may provide further details about their travel requirements, such as the number of travellers, number of rooms required, preferred hotel facilities, proximity to shopping malls or metro stations, and nearby amenities such as 24-hour convenience stores.

3.Use of AI
3.1 How AI is utilised in the application
Hotel scoring and selection : AI processes budget and preferences of users to output top 3 results based on suitability score.
Automated nearby sourcing : System lists places of interest and food options for the top 3 hotels generated respectively.
Data storage and usage : User inputs and outputs generated will be logged into JSON file and sent to the user’s email

3.2 AI inputs, outputs and sample recommendation
System inputs:
Mandatory fields: Destination (country, city), budget range (SGD), user email address.
Elaborative preference field: Natural language text detailing group size, room configurations, specific amenities (e.g. bathtubs) and proximity preferences (e.g. metro stations, bus stops and convenience stores).

Generated outputs and insights:
Top 3 hotel selections: The best matching properties, displaying location (country, city) and per night price (in SGD, excluding fees).
Local guide: Provides nearby food options and activities for each recommended hotel.
Email & JSON output: A structured summary sent directly to the user's inbox for personal reference and additionally stored in a database file for future use.

4.Business Rules
4.1 Input Validation Rules
Mandatory inputs: The form rejects submission if destination, budget or email is missing.
Budget formatting: Budget must be in positive SGD values.
Email format: Email inputs must match standard syntax (e.g. name@example.com).

4.2 AI output & Scoring Rules
Strict price cap: Hotels exceeding the user's maximum budget will be excluded.
No duplication: Recommendations must feature 3 distinct properties (no same duplicate listings for different room types).
Quality: Exclude hotels rated below 3.5/5 stars unless no other options exist within budget.
Location: Distance claims (e.g "MRT within 500m") must be verified against actual location data on a map before scoring, the AI will not just trust the hotel's text description

4.3 Fallback logic (when the app loses connection to external databases or APIs)
Removing constraint: If no hotel matches 100% of criteria, non-essential amenities (e.g. bathtubs) are dropped first, keeping the budget and destination fixed and prioritised.
User alert: Displays a clear notice if relaxed criteria were used: "We could not find a hotel matching all your requests, but here are the best options within your budget."
Missing nearby data: If local food or attraction data fails to load, standard city-centre highlights are shown instead of empty fields (Error 404).
