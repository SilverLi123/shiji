#include <stddef.h>
#include <stdint.h>
int shiji_inflate(const uint8_t *input, size_t count, uint8_t *output, size_t size);
uint32_t shiji_crc(const uint8_t *input, size_t count);
