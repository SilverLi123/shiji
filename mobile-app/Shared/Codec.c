#include "Codec.h"
#include <zlib.h>
#include <limits.h>
int shiji_inflate(const uint8_t *input,size_t count,uint8_t *output,size_t size){
 if(count>UINT_MAX||size>UINT_MAX)return 0;
 z_stream s={0};s.next_in=(Bytef*)input;s.avail_in=(uInt)count;s.next_out=output;s.avail_out=(uInt)(size?size:1);
 if(inflateInit2(&s,-MAX_WBITS)!=Z_OK)return 0;
 int result=inflate(&s,Z_FINISH);int ok=result==Z_STREAM_END&&s.total_out==size&&s.total_in==count;inflateEnd(&s);return ok;
}
uint32_t shiji_crc(const uint8_t *input,size_t count){return (uint32_t)crc32(0,input,(uInt)count);}
