
# Meetup data exporter

## Problem statement

I need to export data from my Meetup page, and it contains: 
- past events with all the details,
- events cover photos, 
- list of attendees for each event.

## Instructions 

I need a Python project with folder structure that will automate the export of the data because I do not have PRO version and I do not have API access.

Here is how I envision folder structure:
- events/ - folder that contains events data
  - events/<event_date>_<event_id>_<event_slug> - folder for each event
    - cover_photo - cover photo for that event with appropriate extension
    - attendees_<event_id>.csv - file that contains exported list of attendees
  -  events.csv - CSV file that contains events data, and should include: id, title, event_url, description, venue_name, venue_address, venue_city, venue_country, date_time, created_time, end_time, going_count, featured_photo_url, cover_image
- json/ - folder where events JSON documents related to events should be downloaded
- assets/
  - group_info.md - brief Meetup group description
  - group_cover.jpeg - group cover image
  - events_data_schema.json - JSON schema for events JSON documents 

Since I do not have API access, you will simulate API calls that browser is making when fetching events data for display. 
After you get the content you will save each JSON document in @json/ folder.
You have to create Pydantic models for validating and extracting data from these.
Once you validate and extract required data, you can create events.csv and put it in above defined folder.
event_slug part of each event's folder should be a slugified version of trimmed event title to first 40 characters.

### Simulating API calls to get events data

Create a Python script that will initiate events data download. 
Each HTTP request needs to use POST method and EVENTS_API_URL is 'https://www.meetup.com/gql2'.
Payload you have to use is the following:

```json
{
    "operationName": "getPastGroupEvents",
    "variables": {
        "urlname": "data-science-club-belgrade",
        "beforeDateTime": "2026-02-13T15:22:54.291Z",
        "after": "Mjk2NDk1NDMwOjE2OTcyMTI4MDAwMDA="
    },
    "extensions": {
        "persistedQuery": {
            "version": 1,
            "sha256Hash": "9463f7c9ab5b08db3f2172223c806fb48993508781cd939184d9151c75214e3a"
        }
    }
}
```

Now, the variables.urlname needs to be provided as a slugified title of the Meetup group. Python script has to take that as an argument.
variables.beforeDateTime needs to be ISO version of the current date and time.
variables.after is optional. In case it exists it can be used for requesting next page of events i.e. next JSON document.

After issuing POST HTTP request, the response is a JSON document with the schema defined in @assets/events_data_schema.json file.
You have to save this document in @json/ folder for later use.
If in this document data.groupByUrlname.events.pageInfo.hasNextPage is 'true', you have to use data.groupByUrlname.events.pageInfo.endCursor value and make another request replacing variables.after with this value. 
This way you paginate through the events list. 
You have to paginate as long as there is a next page, and you have to save each of the JSON documents you get as a response.

After you finish downloading events data in files inside @json/, you will find that events data is located in data.groupByUrlname.events.edges as an array of JSON documents in each of the saved JSON files. 
You have to create Pydantic models for validating and extracting events data.
Once the data is validated and extracted you need to save it to events.csv folder located in above defined folder location.

### Simulating API calls to get attendees data

Attendees list is created by issuing HTTP POST request to Meetup's server, with the following JSON payload:

```json
{
  "operationName":"generateEventAttendeesReport",
  "variables":{
    "eventId":"..."
  },
  "extensions":{
    "persistedQuery":{
      "version":1,
      "sha256Hash":"f7c9409796ae0724dadeaf075b883c3e6e19438387dd2c064bc075f6413a3d0e"}
  }
}
```

You have to replace "eventID" with each event's ID, and then POST it to the following ATTENDEES_API_URL: https://www.meetup.com/gql2

The response you will get is the following JSON document:

```json
{
	"data": {
		"generateEventAttendeesReport": {
			"url": "...",
			"__typename": "GenerateEventAttendeesReportPayload"
		}
	}
}
```

The data.generateEventAttendeesReport.url will contain the URL to CSV file that contains attendees list. 
You have to download this CSV file and put it in previously defined folder.

## Data model

Each JSON file in @json/ will have a JSON document with the same structure.
The data you will need is nested under data.groupByUrlname.events.edges, and each event will be a nested document. 

The way you will map document values to Pydantic model fields is:
- id -> event_id
- title -> title
- eventURL -> event_url
- description -> description 
- venue.name -> venue_name, 
- venue.address -> venue_address, 
- venue.city -> venue_city, 
- venue.country -> venue_country, 
- dateTime -> date_time, 
- createdTime -> created_time, 
- endTime -> end_time, 
- going.totalCount -> going_count, 
- featuredEventPhoto.highResUrl -> featured_photo_url,

I need you to add additional field that will hold a path to a cover photo saved for each event. 
That is why each model needs to have "cover_image" field, and the CSV file that contains all events data needs to have this column as well.

## Implementation details

You have to use following Python libraries:
- pydantic - for JSON documents validation and export to CSV file.
- httpx - for issuing HTTP requests.
- loguru - for logging.
- tqdm - for drawing progress bar each time you iterate in downloading multiple files.

Important: Do not impose any library versions. Just put them in a requirements.txt and let dependencies be resolved by the tool e.g. pip.

I want two Python scripts.

First Python script, named `get_events_data.py` has to:
- accept an argument that represents Meetup group name
- download all events in @json/ folder

Second Python script, named `process_events.py` has to:
- validate and extract data from JSON documents in @json/ folder
- download cover images
- save events data in defined @events/ folder
- download attendees CSV files for each event
- make sure you implement graceful error handling i.e. continue with the process in case there is an error for particular event

Python script has to skip processing events if events data already exists. 
The same applies to attendees CSV files.
The goal is to not overload Meetup server with repeated downloads if the files are already downloaded.

In the process of issuing HTTP requests make sure you have:
- cookie set when issuing requests towards Meetup's servers. Cookie value is provided in @.cookie file. 
- sleep time between each successive request, e.g. random sleep between 1 and 3 seconds.
- retry mechanism with up to three retries, with the sleep time between each request as well

I want to log all HTTP requests that are being issued, as well as response statuses as well.
In case response status is not 20X, I need to know what is happening so do log response content under the ERROR level.
Each time status is 20X log it under the INFO level.

## Output

Once I submit this specification to you, you will:
- create a detailed plan of what you will do and the steps you will follow
- once I approve the plan you will save it under the PLAN.md
- start with the implementation per my specification
- read @PLAN.md and Python scripts and check if everything is implemented as specified. Write a thorough report on deliverables and features not covered in current implementation in @DELIVERY_REPORT.md Markdown file.
- update CLAUDE.md
- create friendly README.md file that will be a landing page on GitHub that describes the purpose of the project, folder structure and their purpose, purpose of runnable Python scripts with examples on how to run them, and licensing part that references MIT license. You can use @assets/group_info.md as brief information about the Meetup group, and @assets/group_cover.jpeg as a group image.


