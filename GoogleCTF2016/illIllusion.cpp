#include <iostream>

using namespace cv;

#define _WORD unsigned short
#define _DWORD unsigned int

char byte_A20[]={0x4A,0x49,0x59,0x6C,0x45,0x4C,0x7F,0x5B,0x78,0x6A,0x60,0x7A,0x75,0x78,0x60,0x6E,0x7F,0x4F,0x76,0x7F,0x7A,0x66,0x4F,0x41,0x52,0x6B,0x69,0x50,0x6B,0x59,0x6D,0x62,0x46,0x66,0x74,0x4B,0x71,0x75,0x73,0x66,0x6E,0x7D,0x66,0x6C,0x68,0x51,0x66,0x73,0x71,0x78,0x72,0x5C,0x54,0x65,0x61,0x53,0x67,0x6E,0x6D,0x64,0x63,0x21,0x0};

int main(int argc, char *argv[])
{

     char v5[100] = "TRytfrgooq|F{i-JovFBungFk\\VlphgQbwvj~HuDgaeTzuSt.@Lex^~\x00"; // ebp@1
     const char *v7="ZGFkNGIwYzIWYjEzMTUWNjVjNTVlNjZhOGJkNhYtODIyOGEaMTMWNmQaOTVjZjkhMzRjYmUzZGE?"; // [sp+14h] [bp-168h]@1
     const char *v8="MzQxZTZmZjAxMmIiMWUzNjUxMmRiYjIxNDUwYTUxMWItZGQzNWUtMzkyOWYyMmQeYjZmMzEaNDQ?"; // [sp+18h] [bp-164h]@1

     int v6; // ebp@1
     size_t v9; // eax@1
     int v10; // edi@1
     char v11; // al@2
     int result; // eax@3
     char v13[76]; // [sp+28h] [bp-154h]@1
     char v14; // [sp+74h] [bp-108h]@1
     char v15[76]; // [sp+75h] [bp-107h]@1
     char v16; // [sp+C1h] [bp-BBh]@1
     char dest[76]; // [sp+C2h] [bp-BAh]@1
     char v18; // [sp+10Eh] [bp-6Eh]@1
     char v19[76]; // [sp+10Fh] [bp-6Dh]@2
     char v20; // [sp+15Bh] [bp-21h]@3
     int v21; // [sp+15Ch] [bp-20h]@1

     v9 = (size_t)&v5[strlen(v5)];
       *(_DWORD *)v9 = 'Gwnw';
       *(_DWORD *)(v9 + 4) = '{bar';
       *(_DWORD *)(v9 + 8) = 'btuO';
       *(_DWORD *)(v9 + 12) = 'Crh';
       *(_DWORD *)(v9 + 16) = 'mqft';
       *(_WORD *)(v9 + 20) = 125;
       strncpy(dest, v5, 0x4Cu);
       strncpy(v13, v7, 0x4Cu);
       strncpy(v15, v8, 0x4Cu);
       v18 = 0;
       v16 = 0;
       v10 = 0;
       v14 = 0;
       do
       {
         v11 = dest[v10] ^ v13[v10] ^ v15[v10];
         v19[v10++] = v11;
         printf("%c", v11);
       }
       while ( v10 != 76 );
      //printf("Here is your Reply: %s", v25);

      return 0;
}
