from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


# --- API Response Models (match assets/events_data_schema.json) ---


class PageInfo(BaseModel):
    endCursor: str
    hasNextPage: bool


class Venue(BaseModel):
    id: str
    name: str
    address: str
    city: str
    state: str
    country: str


class Going(BaseModel):
    totalCount: int


class FeaturedEventPhoto(BaseModel):
    id: str
    baseUrl: str
    highResUrl: str


class EventNode(BaseModel):
    id: str
    title: str
    eventUrl: str
    description: str
    venue: Optional[Venue] = None
    dateTime: str
    createdTime: str
    endTime: str
    going: Going
    featuredEventPhoto: Optional[FeaturedEventPhoto] = None


class EventEdge(BaseModel):
    node: EventNode


class Events(BaseModel):
    totalCount: int
    pageInfo: PageInfo
    edges: list[EventEdge]


class GroupByUrlname(BaseModel):
    id: str
    events: Events


class DataWrapper(BaseModel):
    groupByUrlname: GroupByUrlname


class EventsApiResponse(BaseModel):
    data: DataWrapper


# --- Export Model (flattened for CSV) ---


class EventRecord(BaseModel):
    event_id: str
    title: str
    event_url: str
    description: str
    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    venue_city: Optional[str] = None
    venue_country: Optional[str] = None
    date_time: str
    created_time: str
    end_time: str
    going_count: int
    featured_photo_url: Optional[str] = None
    cover_image: Optional[str] = None

    @classmethod
    def from_event_node(cls, node: EventNode, cover_image: str = "") -> EventRecord:
        return cls(
            event_id=node.id,
            title=node.title,
            event_url=node.eventUrl,
            description=node.description,
            venue_name=node.venue.name if node.venue else None,
            venue_address=node.venue.address if node.venue else None,
            venue_city=node.venue.city if node.venue else None,
            venue_country=node.venue.country if node.venue else None,
            date_time=node.dateTime,
            created_time=node.createdTime,
            end_time=node.endTime,
            going_count=node.going.totalCount,
            featured_photo_url=(
                node.featuredEventPhoto.highResUrl
                if node.featuredEventPhoto
                else None
            ),
            cover_image=cover_image or None,
        )


# --- Attendees Report Response Model ---


class GenerateEventAttendeesReportPayload(BaseModel):
    url: str


class AttendeeReportData(BaseModel):
    generateEventAttendeesReport: GenerateEventAttendeesReportPayload


class AttendeeReportResponse(BaseModel):
    data: AttendeeReportData