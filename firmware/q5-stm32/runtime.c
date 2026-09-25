#include <stddef.h>
void *memset(void *d,int c,size_t n){unsigned char *p=d;while(n--)*p++=(unsigned char)c;return d;}
void *memcpy(void *d,const void *s,size_t n){unsigned char *a=d;const unsigned char *b=s;while(n--)*a++=*b++;return d;}
void *memmove(void *d,const void *s,size_t n){unsigned char *a=d;const unsigned char *b=s;if(a<b)while(n--)*a++=*b++;else{a+=n;b+=n;while(n--)*--a=*--b;}return d;}
void __aeabi_memcpy(void *d,const void *s,size_t n){(void)memcpy(d,s,n);}
void __aeabi_memcpy4(void *d,const void *s,size_t n){(void)memcpy(d,s,n);}
void __aeabi_memclr(void *d,size_t n){(void)memset(d,0,n);}
void __aeabi_memclr4(void *d,size_t n){(void)memset(d,0,n);}
