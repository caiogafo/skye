"""DynamoDB storage backend (moved from routes/storage_backends.py)."""

import json
import time
from typing import Any, Dict, List, Optional, Tuple

from nimbus.base.interfaces import StorageBackend


class DynamoDBBackend(StorageBackend):
    """DynamoDB storage backend for AWS serverless environments."""

    def __init__(self, table_name: str, region_name: str = "us-east-1"):
        """Initialize DynamoDB backend.
        
        Args:
            table_name: DynamoDB table name
            region_name: AWS region
        """
        self.table_name = table_name
        self.region_name = region_name
        self._dynamodb = None

    async def connect(self) -> None:
        """Initialize DynamoDB connection."""
        await self._get_dynamodb()  # This will create the connection

    async def _get_dynamodb(self):
        """Get DynamoDB resource (lazy initialization)."""
        if self._dynamodb is None:
            try:
                import boto3
                self._dynamodb = boto3.resource('dynamodb', region_name=self.region_name)
            except ImportError:
                raise ImportError("boto3 package required for DynamoDBBackend. Install with: pip install boto3")
        return self._dynamodb

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from DynamoDB."""
        dynamodb = await self._get_dynamodb()
        table = dynamodb.Table(self.table_name)
        
        try:
            response = table.get_item(Key={'pk': key})
            item = response.get('Item')
            if item:
                # Remove DynamoDB metadata
                item.pop('pk', None)
                item.pop('ttl', None)
                return item
            return None
        except Exception:
            return None

    async def set(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set data in DynamoDB."""
        dynamodb = await self._get_dynamodb()
        table = dynamodb.Table(self.table_name)
        
        item = {'pk': key, **data}
        if ttl:
            item['ttl'] = int(time.time()) + ttl
        
        table.put_item(Item=item)

    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Atomically increment counter in DynamoDB."""
        dynamodb = await self._get_dynamodb()
        table = dynamodb.Table(self.table_name)
        
        update_expression = "ADD #count :amount"
        expression_attribute_names = {"#count": "count"}
        expression_attribute_values = {":amount": amount}
        
        if ttl:
            update_expression += ", #ttl :ttl"
            expression_attribute_names["#ttl"] = "ttl"
            expression_attribute_values[":ttl"] = int(time.time()) + ttl
        
        response = table.update_item(
            Key={'pk': key},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="NEW"
        )
        
        return response['Attributes']['count']

    async def get_multiple(self, keys: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get multiple keys from DynamoDB."""
        if not keys:
            return {}
        
        dynamodb = await self._get_dynamodb()
        
        # DynamoDB batch_get_item
        request_items = {
            self.table_name: {
                'Keys': [{'pk': key} for key in keys]
            }
        }
        
        response = dynamodb.batch_get_item(RequestItems=request_items)
        items = response.get('Responses', {}).get(self.table_name, [])
        
        result = {key: None for key in keys}
        for item in items:
            key = item.pop('pk')
            item.pop('ttl', None)  # Remove TTL metadata
            result[key] = item
        
        return result

    async def set_multiple(self, data: Dict[str, Dict[str, Any]], ttl: Optional[int] = None) -> None:
        """Set multiple keys in DynamoDB."""
        if not data:
            return
        
        dynamodb = await self._get_dynamodb()
        table = dynamodb.Table(self.table_name)
        
        # Use batch_writer for efficient bulk writes
        with table.batch_writer() as batch:
            for key, value in data.items():
                item = {'pk': key, **value}
                if ttl:
                    item['ttl'] = int(time.time()) + ttl
