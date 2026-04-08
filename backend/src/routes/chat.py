from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat(body: ChatRequest, request: Request):
    try:
        print("Entró en /chat")
        print("Mensaje:", body.message)

        mcp_client = request.app.state.mcp_client
        print("Tengo mcp_client")

        response = await mcp_client.process_query(body.message)
        print("Respuesta generada:", response)

        return {"message": response}
    except Exception as e:
        print("ERROR EN /chat:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))