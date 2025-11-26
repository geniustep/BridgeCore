"""
Schemas for Moodle API operations
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============= Course Schemas =============

class MoodleCourseBase(BaseModel):
    """Base Moodle course schema"""
    fullname: str = Field(..., description="Course full name")
    shortname: str = Field(..., description="Course short name")
    categoryid: int = Field(..., description="Category ID")
    summary: Optional[str] = Field(None, description="Course summary")
    summaryformat: int = Field(default=1, description="Summary format (1=HTML)")
    format: str = Field(default="topics", description="Course format")
    showgrades: int = Field(default=1, description="Show grades")
    newsitems: int = Field(default=5, description="Number of news items")
    startdate: Optional[int] = Field(None, description="Course start date (timestamp)")
    enddate: Optional[int] = Field(None, description="Course end date (timestamp)")
    visible: int = Field(default=1, description="Visibility (1=visible, 0=hidden)")


class MoodleCourseCreate(MoodleCourseBase):
    """Schema for creating Moodle course"""
    pass


class MoodleCourseUpdate(BaseModel):
    """Schema for updating Moodle course"""
    id: int
    fullname: Optional[str] = None
    shortname: Optional[str] = None
    categoryid: Optional[int] = None
    summary: Optional[str] = None
    visible: Optional[int] = None


class MoodleCourseResponse(BaseModel):
    """Moodle course response"""
    id: int
    fullname: str
    shortname: str
    categoryid: int
    categoryname: Optional[str] = None
    summary: Optional[str] = None
    summaryformat: Optional[int] = None
    format: Optional[str] = None
    showgrades: Optional[int] = None
    startdate: Optional[int] = None
    enddate: Optional[int] = None
    visible: Optional[int] = None
    enrolledusercount: Optional[int] = None

    class Config:
        from_attributes = True


# ============= User Schemas =============

class MoodleUserBase(BaseModel):
    """Base Moodle user schema"""
    username: str = Field(..., description="Username (unique)")
    password: str = Field(..., description="User password")
    firstname: str = Field(..., description="First name")
    lastname: str = Field(..., description="Last name")
    email: str = Field(..., description="Email address")
    auth: str = Field(default="manual", description="Authentication method")
    city: Optional[str] = Field(None, description="City")
    country: Optional[str] = Field(None, description="Country code (e.g., US, SA)")
    lang: str = Field(default="en", description="Language code")
    timezone: str = Field(default="UTC", description="Timezone")


class MoodleUserCreate(MoodleUserBase):
    """Schema for creating Moodle user"""
    pass


class MoodleUserUpdate(BaseModel):
    """Schema for updating Moodle user"""
    id: int
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    password: Optional[str] = None


class MoodleUserResponse(BaseModel):
    """Moodle user response"""
    id: int
    username: str
    firstname: str
    lastname: str
    fullname: Optional[str] = None
    email: str
    city: Optional[str] = None
    country: Optional[str] = None
    lang: Optional[str] = None
    timezone: Optional[str] = None
    profileimageurl: Optional[str] = None
    firstaccess: Optional[int] = None
    lastaccess: Optional[int] = None

    class Config:
        from_attributes = True


# ============= Enrolment Schemas =============

class MoodleEnrolmentCreate(BaseModel):
    """Schema for enrolling user in course"""
    courseid: int = Field(..., description="Course ID")
    userid: int = Field(..., description="User ID")
    roleid: int = Field(default=5, description="Role ID (5=student, 3=teacher)")
    timestart: Optional[int] = Field(None, description="Enrolment start time (timestamp)")
    timeend: Optional[int] = Field(None, description="Enrolment end time (timestamp)")
    suspend: int = Field(default=0, description="Suspend enrolment (0=active, 1=suspended)")


class MoodleEnrolmentResponse(BaseModel):
    """Moodle enrolment response"""
    id: int
    courseid: int
    userid: int
    roleid: int
    timestart: Optional[int] = None
    timeend: Optional[int] = None
    suspended: Optional[int] = None


# ============= Category Schemas =============

class MoodleCategoryBase(BaseModel):
    """Base Moodle category schema"""
    name: str = Field(..., description="Category name")
    parent: int = Field(default=0, description="Parent category ID (0=top level)")
    description: Optional[str] = Field(None, description="Category description")
    descriptionformat: int = Field(default=1, description="Description format")


class MoodleCategoryCreate(MoodleCategoryBase):
    """Schema for creating Moodle category"""
    pass


class MoodleCategoryResponse(BaseModel):
    """Moodle category response"""
    id: int
    name: str
    parent: int
    coursecount: Optional[int] = None
    description: Optional[str] = None
    descriptionformat: Optional[int] = None

    class Config:
        from_attributes = True


# ============= Grade Schemas =============

class MoodleGradeItem(BaseModel):
    """Moodle grade item"""
    id: int
    itemname: str
    itemtype: str
    itemmodule: Optional[str] = None
    graderaw: Optional[float] = None
    gradeformatted: Optional[str] = None
    grademin: Optional[float] = None
    grademax: Optional[float] = None
    feedback: Optional[str] = None


class MoodleGradeResponse(BaseModel):
    """Moodle grade response"""
    courseid: int
    userid: int
    userfullname: str
    gradeitems: List[MoodleGradeItem]


# ============= Search Schemas =============

class MoodleSearchCriteria(BaseModel):
    """Search criteria for Moodle"""
    key: str = Field(..., description="Field name (e.g., 'username', 'email')")
    value: str = Field(..., description="Search value")


class MoodleSearchRequest(BaseModel):
    """Moodle search request"""
    model: str = Field(..., description="Entity type (courses, users, etc.)")
    criteria: Optional[List[MoodleSearchCriteria]] = Field(None, description="Search criteria")
    limit: Optional[int] = Field(None, description="Maximum results")


# ============= Batch Operations =============

class MoodleBatchOperation(BaseModel):
    """Single batch operation"""
    operation: str = Field(..., description="Operation type (create, update, delete)")
    model: str = Field(..., description="Entity type")
    data: Dict[str, Any] = Field(..., description="Operation data")


class MoodleBatchRequest(BaseModel):
    """Batch operations request"""
    operations: List[MoodleBatchOperation] = Field(..., description="List of operations")


class MoodleBatchResponse(BaseModel):
    """Batch operations response"""
    success: bool
    results: List[Dict[str, Any]]
    errors: List[str] = []


# ============= Site Info Schemas =============

class MoodleSiteInfo(BaseModel):
    """Moodle site information"""
    sitename: str
    username: str
    firstname: str
    lastname: str
    fullname: str
    userid: int
    siteurl: str
    userpictureurl: str
    functions: Optional[List[Dict[str, Any]]] = None
    release: Optional[str] = None
    version: Optional[str] = None
    mobilecssurl: Optional[str] = None
