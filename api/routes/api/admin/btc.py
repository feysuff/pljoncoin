from fastapi import APIRouter, Depends, Query, Request, Path, HTTPException
from depends import Session, get_db, get_authorized
from models.log import LogHistoryPrivate
from models.user import User
from models.crud import LogEntryCRUD, BlockCRUD, TransactionCRUD
from utils import get_btc_block_transactions

router = APIRouter(prefix='/btc', tags=['BTC', 'User', 'Admin'])

@router.get('/history/{user_id}', response_model=LogHistoryPrivate, summary='Получить историю запросов')
async def get_history(db: Session = Depends(get_db),
                      user: User = Depends(get_authorized),
                      limit: int = Query(10, description='Ограничение количества записей в ответе'),
                      offset: int = Query(0, description='Сдвиг от начала')) -> LogHistoryPrivate:
    return LogEntryCRUD.get_history(db, user.id, offset, limit, public=False)

@router.get('/get/{block_id}', responses={401: {'detail': 'Block not found'}}, response_model=list[str])
async def get_block(request: Request,
                    db: Session = Depends(get_db),
                    block_id: int = Path(..., description='ID блока в сети BTC'),
                    user: User = Depends(get_authorized)) -> list[str]:
    block_bc_id = block_id
    block = BlockCRUD.get(db, block_bc_id=block_bc_id)
    block_id = block.id if block is not None else None
    block = [] if block is None else BlockCRUD.get_transactions(db, block.id)
    if len(block) == 0:
        block = get_btc_block_transactions(block_bc_id)
        if block is None:
            raise HTTPException(401, detail='Block bot found')
        else:
            block_id = BlockCRUD.add(db, Block(bc_id=block_bc_id)).id
            TransactionCRUD.add(db, block_id, *block)
    # LogEntryCRUD.add(db, user.id, block_id, request.client.host)
    return block
