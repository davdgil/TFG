from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat(body: ChatRequest, request: Request):
    try:
        print("Entro en /chat")
        print("Mensaje:", body.message)

        mcp_client = request.app.state.mcp_client
        print("Tengo mcp_client")

        response = await mcp_client.process_query(body.message)
        print("Respuesta generada:", response)

        if isinstance(response, dict):
            return response

        return {
            "message": response,
            "kpis": {},
            "table": [],
            "chart": None,
        }
    except RuntimeError as e:
        print("ERROR CONTROLADO EN /chat:", repr(e))
        return {
            "message": str(e),
            "kpis": {},
            "table": [],
            "chart": None,
        }
    except Exception as e:
        print("ERROR EN /chat:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))
