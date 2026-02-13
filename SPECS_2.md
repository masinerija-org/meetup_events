
# Meetup group overview

## Problem statement

I want to create one pager application with static content. 
There is no backend part of the application.

The data for this web page should be fetched from @assets/ and @events/ folders.

Namely, I want to have a onepager web application that will:
- have a hero section with @assets/group_cover.jpeg image
- title that states the name of the group fetched from @assets/group_info.md
- brief group description fetched from @assets/group_info.md
- events gallery in three columns, where
- each event will be represented with its cover image, title and number of attendees
- on clicking on each of the gallery items, web app should be redirected to a route that displays event information
- below gallery there should be a list of group administrator, taken from @assets/group_info.md, 
- where each administrator card should consist of circle place for avatar and his name, 
- administrators should be presented in 4 x 2 grid,
- there should be copyright statement in footer and it should state that copyrights are stated by Machinery

Event route should have:
- event cover image in hero section
- event title as title
- event description,
- venue name and venue city,
- date_time as the date of event start
- a 'Back' button to return to a landing page

## Implementation details 

Routes should be:
- `/` for landing page 
- `event/<event_id>` for loading event data by its event_id

Web application should be stored in `/web` folder.
For all the data you need to statically provide for web application, use data in @events/ and use Python for any processing.

## Output

Once I submit this specification to you, you will:
- detailed plan of all steps you will execute in creating web app
- once I approve the plan, you will save this plan in PLAN_WEB.md file
- start with the implementation based on my specification
- update CLAUDE.md file
- update README.md file