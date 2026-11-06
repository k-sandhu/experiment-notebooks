using System;
using System.IO;
using System.Text;

class Program
{
    static byte[] b = Array.Empty<byte>();
    static int p, n;
    static byte[] arena = new byte[8192];
    static int arenaLen = 0;
    static byte[] sSrc = Array.Empty<byte>(); static int sOff, sLen;

    static void SkipWs(){ while(p<n){ byte c=b[p]; if(c==' '||c=='\t'||c=='\r'||c=='\n') p++; else break; } }
    static int Hex4(byte[] a,int off){ int v=0; for(int i=0;i<4;i++){ byte c=a[off+i]; v<<=4; if(c>='0'&&c<='9')v|=c-'0'; else if(c>='a'&&c<='f')v|=c-'a'+10; else if(c>='A'&&c<='F')v|=c-'A'+10; } return v; }
    static void DecodeSpan(byte[] src,int s,int e){
        int need=e-s;
        if(arenaLen+need>arena.Length){ int cap=Math.Max(need, arena.Length*2); arena=new byte[cap]; arenaLen=0; }
        int outPos=arenaLen; int i=s;
        while(i<e){
            byte c=src[i];
            if(c!='\\'){ arena[outPos++]=c; i++; continue; }
            i++; if(i>=e) break;
            byte esc=src[i++];
            switch(esc){
                case (byte)'"': arena[outPos++]=(byte)'"'; break;
                case (byte)'\\': arena[outPos++]=(byte)'\\'; break;
                case (byte)'/': arena[outPos++]=(byte)'/'; break;
                case (byte)'b': arena[outPos++]= (byte)'\b'; break;
                case (byte)'f': arena[outPos++]=(byte)'\f'; break;
                case (byte)'n': arena[outPos++]=(byte)'\n'; break;
                case (byte)'r': arena[outPos++]=(byte)'\r'; break;
                case (byte)'t': arena[outPos++]=(byte)'\t'; break;
                case (byte)'u': {
                    int cp=Hex4(src,i); i+=4;
                    if(cp>=0xD800&&cp<=0xDBFF&&i+1<e&&src[i]=='\\'&&src[i+1]=='u'){ int lo=Hex4(src,i+2); if(lo>=0xDC00&&lo<=0xDFFF){ i+=6; cp=0x10000+((cp-0xD800)<<10)+(lo-0xDC00); } }
                    if(cp<0x80) arena[outPos++]=(byte)cp;
                    else if(cp<0x800){ arena[outPos++]=(byte)(0xC0|(cp>>6)); arena[outPos++]=(byte)(0x80|(cp&63)); }
                    else if(cp<0x10000){ arena[outPos++]=(byte)(0xE0|(cp>>12)); arena[outPos++]=(byte)(0x80|((cp>>6)&63)); arena[outPos++]=(byte)(0x80|(cp&63)); }
                    else { arena[outPos++]=(byte)(0xF0|(cp>>18)); arena[outPos++]=(byte)(0x80|((cp>>12)&63)); arena[outPos++]=(byte)(0x80|((cp>>6)&63)); arena[outPos++]=(byte)(0x80|(cp&63)); }
                    break; }
                default: arena[outPos++]=esc; break;
            }
        }
        sSrc=arena; sOff=arenaLen; sLen=outPos-arenaLen; arenaLen=outPos;
    }
    static void ParseString(){
        p++; int start=p; int i=p; bool esc=false;
        while(i<n){ byte c=b[i]; if(c=='"') break; if(c=='\\'){ esc=true; i+=2; continue; } i++; }
        p=(i<n)?i+1:i;
        if(!esc){ sSrc=b; sOff=start; sLen=i-start; } else DecodeSpan(b,start,i);
    }
    static bool SpanEq(byte[] lit){ if(sLen!=lit.Length) return false; for(int i=0;i<sLen;i++) if(sSrc[sOff+i]!=lit[i]) return false; return true; }
    static bool SpanEq2(byte[] src,int off,int len, byte[] lit){ if(len!=lit.Length) return false; for(int i=0;i<len;i++) if(src[off+i]!=lit[i]) return false; return true; }
    static bool BytesEq(byte[] a,int ao, byte[] c,int co,int len){ for(int i=0;i<len;i++) if(a[ao+i]!=c[co+i]) return false; return true; }
    static int SpanHash(byte[] src,int off,int len){ ulong h=1469598103934665603UL; for(int i=0;i<len;i++){ h^=src[off+i]; h*=1099511628211UL; } h^=h>>33; h*=0xff51afd7ed558ccdUL; h^=h>>33; return (int)h; }
    static void SkipString(){ p++; while(p<n){ byte c=b[p]; if(c=='"'){p++;return;} if(c=='\\'){p+=2;continue;} p++; } }
    static void SkipValue(){
        SkipWs(); if(p>=n) return; byte c=b[p];
        if(c=='"'){ SkipString(); return; }
        if(c=='{'||c=='['){ int depth=0; while(p<n){ byte ch=b[p]; if(ch=='"'){SkipString();continue;} if(ch=='{'||ch=='['){depth++;p++;continue;} if(ch=='}'||ch==']'){p++; if(--depth==0) return; continue;} p++; } return; }
        while(p<n){ byte ch=b[p]; if(ch==','||ch=='}'||ch==']'||ch==' '||ch=='\t'||ch=='\r'||ch=='\n') break; p++; }
    }
    static long ParseIntValue(){ SkipWs(); bool neg=false; if(p<n&&b[p]=='-'){neg=true;p++;} long v=0; while(p<n&&b[p]>='0'&&b[p]<='9'){ v=v*10+(b[p]-'0'); p++; } while(p<n){ byte c=b[p]; if((c>='0'&&c<='9')||c=='.'||c=='e'||c=='E'||c=='+'||c=='-') p++; else break; } return neg?-v:v; }
    static long ParseAmount(byte[] src,int off,int len){ long v=0; int i=0; while(i<len&&src[off+i]>='0'&&src[off+i]<='9'){ v=v*10+(src[off+i]-'0'); i++; } v*=100; if(i<len&&src[off+i]=='.'){ i++; int frac=0,dig=0; while(i<len&&src[off+i]>='0'&&src[off+i]<='9'&&dig<2){ frac=frac*10+(src[off+i]-'0'); i++; dig++; } if(dig==1) frac*=10; v+=frac; } return v; }

    // account table
    static byte[][] tSrc = Array.Empty<byte[]>(); static int[] tOff=Array.Empty<int>(),tLen=Array.Empty<int>(),tHash=Array.Empty<int>(); static long[] tVal=Array.Empty<long>(); static bool[] tUsed=Array.Empty<bool>(); static int tSize,tMask;
    static void TableInit(int cap){ tSrc=new byte[cap][]; tOff=new int[cap]; tLen=new int[cap]; tHash=new int[cap]; tVal=new long[cap]; tUsed=new bool[cap]; tSize=0; tMask=cap-1; }
    static void TableGrow(){ var oS=tSrc; var oO=tOff; var oL=tLen; var oH=tHash; var oV=tVal; var oU=tUsed; TableInit(oS.Length*2); for(int i=0;i<oS.Length;i++) if(oU[i]){ int idx=oH[i]&tMask; while(tUsed[idx]) idx=(idx+1)&tMask; tUsed[idx]=true; tSrc[idx]=oS[i]; tOff[idx]=oO[i]; tLen[idx]=oL[i]; tHash[idx]=oH[i]; tVal[idx]=oV[i]; tSize++; } }
    static void TableAdd(byte[] src,int off,int len,long delta){
        int h=SpanHash(src,off,len);
        if((tSize+1)*10 > tSrc.Length*7) TableGrow();
        int idx=h&tMask;
        while(true){
            if(!tUsed[idx]){ tUsed[idx]=true; tSrc[idx]=src; tOff[idx]=off; tLen[idx]=len; tHash[idx]=h; tVal[idx]=delta; tSize++; return; }
            if(tHash[idx]==h&&tLen[idx]==len&&BytesEq(tSrc[idx],tOff[idx],src,off,len)){ tVal[idx]+=delta; return; }
            idx=(idx+1)&tMask;
        }
    }
    static int CompareSpan(byte[] a,int ao,int al, byte[] c,int co,int cl){ int l=Math.Min(al,cl); for(int i=0;i<l;i++){ int d=a[ao+i]-c[co+i]; if(d!=0) return d; } return al-cl; }

    static readonly byte[] L_ACCOUNT=Encoding.ASCII.GetBytes("account"), L_TYPE=Encoding.ASCII.GetBytes("type"), L_AMOUNT=Encoding.ASCII.GetBytes("amount"), L_CURRENCY=Encoding.ASCII.GetBytes("currency"), L_TAGS=Encoding.ASCII.GetBytes("tags"), L_META=Encoding.ASCII.GetBytes("meta"), L_RATES=Encoding.ASCII.GetBytes("rates"), L_CHANNEL=Encoding.ASCII.GetBytes("channel"), L_VOID=Encoding.ASCII.GetBytes("void"), L_DEBIT=Encoding.ASCII.GetBytes("debit"), L_TEST=Encoding.ASCII.GetBytes("test");

    static void Main(string[] args){
        b = File.ReadAllBytes(args[0]);
        n=b.Length; p=0;
        if(n==0){ Console.Out.Write("counted 0\nnet 0\n"); return; }
        byte[][] rSrc=new byte[64][]; int[] rOff=new int[64],rLen=new int[64]; long[] rVal=new long[64]; int rCount=0;
        TableInit(1<<16);
        byte[][] cSrc=new byte[64][]; int[] cOff=new int[64],cLen=new int[64]; long[] cCnt=new long[64],cNet=new long[64]; int cCount=0;

        SkipWs();
        if(p<n&&b[p]=='{'){
            p++;
            while(p<n){
                SkipWs(); if(p>=n)break;
                if(b[p]=='}'){p++;break;}
                if(b[p]==','){p++;continue;}
                ParseString(); byte[] kS=sSrc; int kO=sOff,kL=sLen;
                SkipWs(); if(p<n&&b[p]==':')p++;
                if(SpanEq2(kS,kO,kL,L_RATES)){
                    SkipWs();
                    if(p<n&&b[p]=='{'){
                        p++;
                        while(p<n){
                            SkipWs(); if(p>=n)break;
                            if(b[p]=='}'){p++;break;}
                            if(b[p]==','){p++;continue;}
                            ParseString(); byte[] cs=sSrc; int co=sOff,cl=sLen;
                            SkipWs(); if(p<n&&b[p]==':')p++;
                            long rate=ParseIntValue();
                            if(rCount==rSrc.Length){ Array.Resize(ref rSrc,rSrc.Length*2); Array.Resize(ref rOff,rOff.Length*2); Array.Resize(ref rLen,rLen.Length*2); Array.Resize(ref rVal,rVal.Length*2); }
                            rSrc[rCount]=cs; rOff[rCount]=co; rLen[rCount]=cl; rVal[rCount]=rate; rCount++;
                        }
                    } else SkipValue();
                } else SkipValue();
            }
        }

        long counted=0,totalNet=0;
        while(true){
            while(p<n&&(b[p]=='\n'||b[p]=='\r'||b[p]==' '||b[p]=='\t')) p++;
            if(p>=n) break;
            if(b[p]!='{'){ while(p<n&&b[p]!='\n') p++; continue; }
            p++;
            byte[]? aSrc=null; int aOff=0,aLen=0;
            byte[]? chSrc=null; int chOff=0,chLen=0;
            long hundredths=0, rate=1000000; int sign=1; bool skip=false;
            while(p<n){
                SkipWs(); if(p>=n)break;
                byte c=b[p];
                if(c=='}'){p++;break;}
                if(c==','){p++;continue;}
                ParseString();
                byte[] kS=sSrc; int kO=sOff,kL=sLen;
                int kid=-1;
                if(kL==7&&SpanEq2(kS,kO,kL,L_ACCOUNT)) kid=0;
                else if(kL==4&&SpanEq2(kS,kO,kL,L_TYPE)) kid=1;
                else if(kL==6&&SpanEq2(kS,kO,kL,L_AMOUNT)) kid=2;
                else if(kL==8&&SpanEq2(kS,kO,kL,L_CURRENCY)) kid=3;
                else if(kL==4&&SpanEq2(kS,kO,kL,L_TAGS)) kid=4;
                else if(kL==4&&SpanEq2(kS,kO,kL,L_META)) kid=5;
                SkipWs(); if(p<n&&b[p]==':')p++; SkipWs();
                switch(kid){
                    case 0: if(p<n&&b[p]=='"'){ ParseString(); aSrc=sSrc;aOff=sOff;aLen=sLen; } else SkipValue(); break;
                    case 1: if(p<n&&b[p]=='"'){ ParseString(); if(SpanEq(L_VOID)) skip=true; else if(SpanEq(L_DEBIT)) sign=-1; else sign=1; } else SkipValue(); break;
                    case 2: if(p<n&&b[p]=='"'){ ParseString(); hundredths=ParseAmount(sSrc,sOff,sLen); } else SkipValue(); break;
                    case 3: if(p<n&&b[p]=='"'){ ParseString(); rate=0; for(int i=0;i<rCount;i++) if(rLen[i]==sLen&&BytesEq(rSrc[i],rOff[i],sSrc,sOff,sLen)){ rate=rVal[i]; break; } } else SkipValue(); break;
                    case 4: {
                        SkipWs();
                        if(p<n&&b[p]=='['){ p++; while(p<n){ SkipWs(); if(p>=n)break; if(b[p]==']'){p++;break;} if(b[p]==','){p++;continue;} if(b[p]=='"'){ ParseString(); if(SpanEq(L_TEST)) skip=true; } else SkipValue(); if(skip) break; } }
                        else SkipValue();
                        break; }
                    case 5: {
                        SkipWs();
                        if(p<n&&b[p]=='{'){ p++; while(p<n){ SkipWs(); if(p>=n)break; if(b[p]=='}'){p++;break;} if(b[p]==','){p++;continue;} ParseString(); byte[] mS=sSrc; int mO=sOff,mL=sLen; bool isCh=SpanEq2(mS,mO,mL,L_CHANNEL); SkipWs(); if(p<n&&b[p]==':')p++; SkipWs(); if(isCh){ if(p<n&&b[p]=='"'){ ParseString(); chSrc=sSrc;chOff=sOff;chLen=sLen; } else SkipValue(); } else SkipValue(); } }
                        else SkipValue();
                        break; }
                    default: SkipValue(); break;
                }
                if(skip){ while(p<n&&b[p]!='\n') p++; if(p<n) p++; break; }
            }
            if(skip) continue;
            long usd=(hundredths*rate)/1000000L;
            long signed=sign*usd;
            counted++; totalNet+=signed;
            if(chSrc!=null){
                int idx=-1;
                for(int i=0;i<cCount;i++) if(cLen[i]==chLen&&BytesEq(cSrc[i],cOff[i],chSrc,chOff,chLen)){ idx=i; break; }
                if(idx<0){ if(cCount==cSrc.Length){ Array.Resize(ref cSrc,cSrc.Length*2); Array.Resize(ref cOff,cOff.Length*2); Array.Resize(ref cLen,cLen.Length*2); Array.Resize(ref cCnt,cCnt.Length*2); Array.Resize(ref cNet,cNet.Length*2); } idx=cCount++; cSrc[idx]=chSrc; cOff[idx]=chOff; cLen[idx]=chLen; }
                cCnt[idx]++; cNet[idx]+=signed;
            }
            if(aSrc!=null) TableAdd(aSrc,aOff,aLen,signed);
        }

        int[] cIdx=new int[cCount]; for(int i=0;i<cCount;i++)cIdx[i]=i;
        Array.Sort(cIdx,(x,y)=>CompareSpan(cSrc[x],cOff[x],cLen[x],cSrc[y],cOff[y],cLen[y]));
        int sz=tSize;
        byte[][] aSrcA=new byte[sz][]; int[] aOffA=new int[sz],aLenA=new int[sz]; long[] aValA=new long[sz]; int ai=0;
        for(int i=0;i<tSrc.Length;i++) if(tUsed[i]){ aSrcA[ai]=tSrc[i]; aOffA[ai]=tOff[i]; aLenA[ai]=tLen[i]; aValA[ai]=tVal[i]; ai++; }
        int[] aIdx=new int[sz]; for(int i=0;i<sz;i++)aIdx[i]=i;
        Array.Sort(aIdx,(x,y)=>{ if(aValA[x]!=aValA[y]) return aValA[x]>aValA[y]?-1:1; return CompareSpan(aSrcA[x],aOffA[x],aLenA[x],aSrcA[y],aOffA[y],aLenA[y]); });

        // Build output as bytes to preserve raw UTF-8 of names
        using var ms=new MemoryStream(8192);
        void WriteStr(string s){ var bytes=Encoding.ASCII.GetBytes(s); ms.Write(bytes,0,bytes.Length); }
        void WriteSpan(byte[] src,int off,int len){ ms.Write(src,off,len); }
        WriteStr($"counted {counted}\n");
        WriteStr($"net {totalNet}\n");
        for(int ii=0;ii<cCount;ii++){ int i=cIdx[ii]; WriteStr("channel "); WriteSpan(cSrc[i],cOff[i],cLen[i]); WriteStr($" {cCnt[i]} {cNet[i]}\n"); }
        int top=Math.Min(10,sz);
        for(int ii=0;ii<top;ii++){ int i=aIdx[ii]; WriteStr("account "); WriteSpan(aSrcA[i],aOffA[i],aLenA[i]); WriteStr($" {aValA[i]}\n"); }
        var outBytes=ms.ToArray();
        using var stdout=Console.OpenStandardOutput();
        stdout.Write(outBytes,0,outBytes.Length);
        stdout.Flush();
    }
}
