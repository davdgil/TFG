from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import time

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat(body: ChatRequest, request: Request):
    started_at = time.perf_counter()
    try:
        print("Entro en /chat")
        print("Mensaje:", body.message)

        mcp_client = request.app.state.mcp_client
        print("Tengo mcp_client")

        response = await mcp_client.process_query(body.message)
        print("Respuesta generada:", response)

        return response
    except RuntimeError as e:
        print("ERROR CONTROLADO EN /chat:", repr(e))
        allowed_functions = mcp_client.infer_allowed_functions(body.message)
        query_mode = mcp_client.infer_query_mode(body.message, allowed_functions)
        latency_ms = round((time.perf_counter() - started_at) * 1000)
        return {
            "message": str(e),
            "kpis": {},
            "table": [],
            "chart": None,
            "meta": {
                "query_mode": query_mode,
                "selected_tool": None,
                "selected_tools": [],
                "tool_calls": 0,
                "latency_ms": latency_ms,
                "had_error": True,
            },
        }
    except Exception as e:
        print("ERROR EN /chat:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))
