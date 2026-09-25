import os
import uuid
import tempfile
import subprocess
from typing import List, get_args
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.utilisateur import User
from app.models.farm import Farm
from app.models.parcel import Parcel
from app.models.raster import Raster
from app.schemas.raster import RasterType, RasterUploadResponse, RasterResponse, RasterCurrentResponse
from app.services.b2_storage import upload_file_to_b2, generate_presigned_url