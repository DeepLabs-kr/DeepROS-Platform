import gzip
import zlib
import bz2
import lzma
import logging
from typing import Optional, Dict, Any, Union
from ..config import DataSettings


logger = logging.getLogger(__name__)


class MessageCompressor:
    """Message compression and decompression utilities."""
    
    COMPRESSION_METHODS = {
        'gzip': 'gzip',
        'zlib': 'zlib', 
        'bz2': 'bz2',
        'lzma': 'lzma',
        'none': None
    }
    
    def __init__(self, settings: Optional[DataSettings] = None):
        self.settings = settings or DataSettings()
        self.default_method = 'gzip'
        self.default_level = self.settings.COMPRESSION_LEVEL
    
    def compress(
        self, 
        data: bytes, 
        method: Optional[str] = None, 
        level: Optional[int] = None
    ) -> Dict[str, Any]:
        """Compress data using the specified method."""
        method = method or self.default_method
        level = level or self.default_level
        
        if method is None or method == 'none':
            return {
                'data': data,
                'method': 'none',
                'original_size': len(data),
                'compressed_size': len(data),
                'compression_ratio': 1.0
            }
        
        try:
            if method == 'gzip':
                compressed_data = gzip.compress(data, compresslevel=level)
            elif method == 'zlib':
                compressed_data = zlib.compress(data, level=level)
            elif method == 'bz2':
                compressed_data = bz2.compress(data, compresslevel=level)
            elif method == 'lzma':
                compressed_data = lzma.compress(data, preset=level)
            else:
                raise ValueError(f"Unsupported compression method: {method}")
            
            original_size = len(data)
            compressed_size = len(compressed_data)
            compression_ratio = compressed_size / original_size if original_size > 0 else 1.0
            
            return {
                'data': compressed_data,
                'method': method,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': compression_ratio
            }
            
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            # Return uncompressed data on failure
            return {
                'data': data,
                'method': 'none',
                'original_size': len(data),
                'compressed_size': len(data),
                'compression_ratio': 1.0,
                'error': str(e)
            }
    
    def decompress(
        self, 
        data: bytes, 
        method: Optional[str] = None
    ) -> Dict[str, Any]:
        """Decompress data using the specified method."""
        if method is None:
            # Try to auto-detect compression method
            method = self._detect_compression_method(data)
        
        if method is None or method == 'none':
            return {
                'data': data,
                'method': 'none',
                'decompressed_size': len(data)
            }
        
        try:
            if method == 'gzip':
                decompressed_data = gzip.decompress(data)
            elif method == 'zlib':
                decompressed_data = zlib.decompress(data)
            elif method == 'bz2':
                decompressed_data = bz2.decompress(data)
            elif method == 'lzma':
                decompressed_data = lzma.decompress(data)
            else:
                raise ValueError(f"Unsupported decompression method: {method}")
            
            return {
                'data': decompressed_data,
                'method': method,
                'decompressed_size': len(decompressed_data)
            }
            
        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            return {
                'data': data,
                'method': 'none',
                'decompressed_size': len(data),
                'error': str(e)
            }
    
    def _detect_compression_method(self, data: bytes) -> Optional[str]:
        """Auto-detect compression method from data header."""
        if len(data) < 2:
            return None
        
        # Check for gzip magic number
        if data.startswith(b'\x1f\x8b'):
            return 'gzip'
        
        # Check for zlib magic number
        if data.startswith(b'\x78\x9c') or data.startswith(b'\x78\xda'):
            return 'zlib'
        
        # Check for bzip2 magic number
        if data.startswith(b'BZ'):
            return 'bz2'
        
        # Check for LZMA magic number
        if data.startswith(b'\xfd7zXZ\x00'):
            return 'lzma'
        
        return None
    
    def get_compression_stats(self, data: bytes) -> Dict[str, Any]:
        """Get compression statistics for different methods."""
        stats = {}
        
        for method in self.COMPRESSION_METHODS.keys():
            if method == 'none':
                continue
            
            result = self.compress(data, method=method)
            stats[method] = {
                'compressed_size': result['compressed_size'],
                'compression_ratio': result['compression_ratio'],
                'space_saved': result['original_size'] - result['compressed_size'],
                'space_saved_percent': (1 - result['compression_ratio']) * 100
            }
        
        return stats
    
    def optimize_compression(
        self, 
        data: bytes, 
        target_ratio: float = 0.5,
        max_time_seconds: float = 5.0
    ) -> Dict[str, Any]:
        """Find the best compression method for the data."""
        import time
        
        start_time = time.time()
        best_result = None
        best_method = None
        
        for method in self.COMPRESSION_METHODS.keys():
            if method == 'none':
                continue
            
            # Check if we've exceeded time limit
            if time.time() - start_time > max_time_seconds:
                break
            
            try:
                result = self.compress(data, method=method)
                
                if (best_result is None or 
                    result['compression_ratio'] < best_result['compression_ratio']):
                    best_result = result
                    best_method = method
                
                # If we've achieved target ratio, stop
                if result['compression_ratio'] <= target_ratio:
                    break
                    
            except Exception as e:
                logger.debug(f"Compression method {method} failed: {e}")
                continue
        
        if best_result is None:
            # Fallback to no compression
            best_result = self.compress(data, method='none')
            best_method = 'none'
        
        return {
            'method': best_method,
            'result': best_result,
            'time_taken': time.time() - start_time
        }
    
    def batch_compress(
        self, 
        data_list: list, 
        method: Optional[str] = None
    ) -> list:
        """Compress a list of data items."""
        results = []
        
        for data in data_list:
            if isinstance(data, bytes):
                result = self.compress(data, method=method)
                results.append(result)
            else:
                logger.warning(f"Skipping non-bytes data: {type(data)}")
                results.append(None)
        
        return results
    
    def batch_decompress(
        self, 
        data_list: list, 
        method: Optional[str] = None
    ) -> list:
        """Decompress a list of data items."""
        results = []
        
        for data in data_list:
            if isinstance(data, bytes):
                result = self.decompress(data, method=method)
                results.append(result)
            else:
                logger.warning(f"Skipping non-bytes data: {type(data)}")
                results.append(None)
        
        return results
    
    def validate_compression(self, original_data: bytes, compressed_data: bytes, method: str) -> bool:
        """Validate that compression/decompression works correctly."""
        try:
            # Decompress the compressed data
            decompressed = self.decompress(compressed_data, method=method)
            
            # Check if decompressed data matches original
            return decompressed['data'] == original_data
            
        except Exception as e:
            logger.error(f"Compression validation failed: {e}")
            return False
    
    def get_method_info(self, method: str) -> Dict[str, Any]:
        """Get information about a compression method."""
        info = {
            'name': method,
            'supported': method in self.COMPRESSION_METHODS,
            'description': '',
            'typical_ratio': 1.0,
            'speed': 'medium',
            'memory_usage': 'medium'
        }
        
        if method == 'gzip':
            info.update({
                'description': 'GNU zip compression, good balance of speed and compression',
                'typical_ratio': 0.3,
                'speed': 'fast',
                'memory_usage': 'low'
            })
        elif method == 'zlib':
            info.update({
                'description': 'Zlib compression, similar to gzip',
                'typical_ratio': 0.3,
                'speed': 'fast',
                'memory_usage': 'low'
            })
        elif method == 'bz2':
            info.update({
                'description': 'Bzip2 compression, better compression but slower',
                'typical_ratio': 0.2,
                'speed': 'slow',
                'memory_usage': 'high'
            })
        elif method == 'lzma':
            info.update({
                'description': 'LZMA compression, best compression but slowest',
                'typical_ratio': 0.15,
                'speed': 'very_slow',
                'memory_usage': 'very_high'
            })
        elif method == 'none':
            info.update({
                'description': 'No compression',
                'typical_ratio': 1.0,
                'speed': 'fastest',
                'memory_usage': 'lowest'
            })
        
        return info 