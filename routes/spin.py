import random
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from database import SessionLocal, Spin
from config import PRIZES_WEIGHTS

router = APIRouter()

@router.post("/spin")
async def spin(request: Request):
  data = await request.json()
  username = data.get("username") or "unknown"
  user_id = data.get("user_id")

  db = SessionLocal()
  try:
      names = [p[0] for p in PRIZES_WEIGHTS]
      weights = [p[1] for p in PRIZES_WEIGHTS]
      prize = random.choices(names, weights=weights, k=1)[0]

      row = Spin(
          username=str(username),
          user_id=str(user_id),
          check_number="no-check",
          prize=prize,
      )
      db.add(row)
      db.commit()

      return JSONResponse({"prize": prize, "repeat": False})
  finally:
      db.close()

