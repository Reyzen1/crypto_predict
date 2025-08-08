import asyncio
from app.services.data_sync import DataSyncService

async def run():
    service = DataSyncService()
    result = await service.sync_current_prices()
    print(result)

asyncio.run(run())