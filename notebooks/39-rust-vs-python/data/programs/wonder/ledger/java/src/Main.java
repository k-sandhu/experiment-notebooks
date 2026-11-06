import java.io.*;
import java.nio.file.*;
import java.util.*;

public class Main {
    static byte[] b;
    static int p, n;
    // arena for decoded strings
    static byte[] arena = new byte[8192];
    static int arenaLen = 0;
    // span result: src array + off + len, via static fields
    static byte[] sSrc; static int sOff, sLen;

    static void skipWs() {
        while (p < n) { byte c = b[p]; if (c==' '||c=='\t'||c=='\r'||c=='\n') p++; else break; }
    }
    static int hex4(byte[] a, int off) {
        int v=0;
        for(int i=0;i<4;i++){ byte c=a[off+i]; v<<=4; if(c>='0'&&c<='9')v|=c-'0'; else if(c>='a'&&c<='f')v|=c-'a'+10; else if(c>='A'&&c<='F')v|=c-'A'+10; }
        return v;
    }
    // decode src[s,e) into arena; sets sSrc/sOff/sLen
    static void decodeSpan(byte[] src, int s, int e) {
        int need = e - s;
        if (arenaLen + need > arena.length) {
            int cap = Math.max(need, arena.length*2);
            arena = new byte[cap]; arenaLen = 0;
        }
        int out = arenaLen;
        int i = s;
        while (i < e) {
            byte c = src[i];
            if (c != '\\') { arena[out++] = c; i++; continue; }
            i++; if (i>=e) break;
            byte esc = src[i++];
            switch (esc) {
                case '"': arena[out++]='"'; break;
                case '\\': arena[out++]='\\'; break;
                case '/': arena[out++]='/'; break;
                case 'b': arena[out++]='\b'; break;
                case 'f': arena[out++]='\f'; break;
                case 'n': arena[out++]='\n'; break;
                case 'r': arena[out++]='\r'; break;
                case 't': arena[out++]='\t'; break;
                case 'u': {
                    int cp = hex4(src, i); i += 4;
                    if (cp>=0xD800 && cp<=0xDBFF && i+1<e && src[i]=='\\' && src[i+1]=='u') {
                        int lo = hex4(src, i+2);
                        if (lo>=0xDC00 && lo<=0xDFFF) { i+=6; cp = 0x10000 + ((cp-0xD800)<<10)+(lo-0xDC00); }
                    }
                    if (cp < 0x80) arena[out++]=(byte)cp;
                    else if (cp < 0x800) { arena[out++]=(byte)(0xC0|(cp>>6)); arena[out++]=(byte)(0x80|(cp&63)); }
                    else if (cp < 0x10000) { arena[out++]=(byte)(0xE0|(cp>>12)); arena[out++]=(byte)(0x80|((cp>>6)&63)); arena[out++]=(byte)(0x80|(cp&63)); }
                    else { arena[out++]=(byte)(0xF0|(cp>>18)); arena[out++]=(byte)(0x80|((cp>>12)&63)); arena[out++]=(byte)(0x80|((cp>>6)&63)); arena[out++]=(byte)(0x80|(cp&63)); }
                    break;
                }
                default: arena[out++] = esc; break;
            }
        }
        sSrc = arena; sOff = arenaLen; sLen = out - arenaLen; arenaLen = out;
    }
    // parse string at p
    static void parseString() {
        p++;
        int start = p;
        int i = p;
        boolean esc = false;
        while (i < n) {
            byte c = b[i];
            if (c=='"') break;
            if (c=='\\') { esc=true; i+=2; continue; }
            i++;
        }
        p = (i < n) ? i+1 : i;
        if (!esc) { sSrc=b; sOff=start; sLen=i-start; }
        else decodeSpan(b, start, i);
    }
    static boolean spanEq(byte[] lit) {
        if (sLen != lit.length) return false;
        for (int i=0;i<sLen;i++) if (sSrc[sOff+i]!=lit[i]) return false;
        return true;
    }
    static boolean spanEq(byte[] src,int off,int len, byte[] lit) {
        if (len != lit.length) return false;
        for (int i=0;i<len;i++) if (src[off+i]!=lit[i]) return false;
        return true;
    }
    static int spanHash(byte[] src,int off,int len){
        long h = 0xcbf29ce484222325L;
        for(int i=0;i<len;i++){ h ^= (src[off+i]&0xff); h *= 0x100000001b3L; }
        h ^= h>>>33; h *= 0xff51afd7ed558ccdL; h ^= h>>>33;
        return (int)h;
    }
    static void skipString() {
        p++;
        while (p<n){ byte c=b[p]; if(c=='"'){p++;return;} if(c=='\\'){p+=2;continue;} p++; }
    }
    static void skipValue() {
        skipWs();
        if (p>=n) return;
        byte c=b[p];
        if (c=='"'){ skipString(); return; }
        if (c=='{'||c=='['){
            int depth=0;
            while(p<n){
                byte ch=b[p];
                if(ch=='"'){ skipString(); continue; }
                if(ch=='{'||ch=='['){depth++;p++;continue;}
                if(ch=='}'||ch==']'){p++; if(--depth==0) return; continue;}
                p++;
            }
            return;
        }
        while(p<n){ byte ch=b[p]; if(ch==','||ch=='}'||ch==']'||ch==' '||ch=='\t'||ch=='\r'||ch=='\n') break; p++; }
    }
    static long parseIntValue(){
        skipWs(); boolean neg=false;
        if(p<n && b[p]=='-'){neg=true;p++;}
        long v=0;
        while(p<n && b[p]>='0'&&b[p]<='9'){ v=v*10+(b[p]-'0'); p++; }
        while(p<n){ byte c=b[p]; if((c>='0'&&c<='9')||c=='.'||c=='e'||c=='E'||c=='+'||c=='-') p++; else break; }
        return neg?-v:v;
    }
    static long parseAmount(byte[] src,int off,int len){
        long v=0; int i=0;
        while(i<len && src[off+i]>='0'&&src[off+i]<='9'){ v=v*10+(src[off+i]-'0'); i++; }
        v*=100;
        if(i<len && src[off+i]=='.'){
            i++; int frac=0,dig=0;
            while(i<len && src[off+i]>='0'&&src[off+i]<='9' && dig<2){ frac=frac*10+(src[off+i]-'0'); i++; dig++; }
            if(dig==1) frac*=10;
            v+=frac;
        }
        return v;
    }

    // account hash table
    static byte[][] tSrc; static int[] tOff,tLen,tHash; static long[] tVal; static boolean[] tUsed; static int tSize, tMask;
    static void tableInit(int cap){ tSrc=new byte[cap][]; tOff=new int[cap]; tLen=new int[cap]; tHash=new int[cap]; tVal=new long[cap]; tUsed=new boolean[cap]; tSize=0; tMask=cap-1; }
    static void tableGrow(){
        byte[][] oS=tSrc; int[] oO=tOff,oL=tLen,oH=tHash; long[] oV=tVal; boolean[] oU=tUsed;
        tableInit(oS.length*2);
        for(int i=0;i<oS.length;i++) if(oU[i]){
            int idx=oH[i]&tMask;
            while(tUsed[idx]) idx=(idx+1)&tMask;
            tUsed[idx]=true; tSrc[idx]=oS[i]; tOff[idx]=oO[i]; tLen[idx]=oL[i]; tHash[idx]=oH[i]; tVal[idx]=oV[i]; tSize++;
        }
    }
    static void tableAdd(byte[] src,int off,int len,long delta){
        int h=spanHash(src,off,len);
        if ((tSize+1)*10 > tSrc.length*7) tableGrow();
        int idx=h&tMask;
        while(true){
            if(!tUsed[idx]){
                tUsed[idx]=true; tSrc[idx]=src; tOff[idx]=off; tLen[idx]=len; tHash[idx]=h; tVal[idx]=delta; tSize++; return;
            }
            if(tHash[idx]==h && tLen[idx]==len){
                boolean eq=true; byte[] ts=tSrc[idx]; int to=tOff[idx];
                for(int i=0;i<len;i++) if(ts[to+i]!=src[off+i]){eq=false;break;}
                if(eq){ tVal[idx]+=delta; return; }
            }
            idx=(idx+1)&tMask;
        }
    }

    static final byte[] L_ACCOUNT="account".getBytes(), L_TYPE="type".getBytes(), L_AMOUNT="amount".getBytes(),
        L_CURRENCY="currency".getBytes(), L_TAGS="tags".getBytes(), L_META="meta".getBytes(), L_RATES="rates".getBytes(),
        L_CHANNEL="channel".getBytes(), L_VOID="void".getBytes(), L_DEBIT="debit".getBytes(), L_TEST="test".getBytes();

    public static void main(String[] args) throws Exception {
        b = Files.readAllBytes(Path.of(args[0]));
        n = b.length; p = 0;
        if (n==0){ System.out.print("counted 0\nnet 0\n"); return; }
        // rates: small arrays
        byte[][] rSrc = new byte[64][]; int[] rOff=new int[64], rLen=new int[64]; long[] rVal=new long[64]; int rCount=0;
        tableInit(1<<16);
        // channels
        byte[][] cSrc=new byte[64][]; int[] cOff=new int[64], cLen=new int[64]; long[] cCnt=new long[64], cNet=new long[64]; int cCount=0;

        skipWs();
        if (p<n && b[p]=='{'){
            p++;
            while(p<n){
                skipWs(); if(p>=n)break;
                if(b[p]=='}'){p++;break;}
                if(b[p]==','){p++;continue;}
                parseString();
                byte[] kS=sSrc; int kO=sOff,kL=sLen;
                skipWs(); if(p<n&&b[p]==':')p++;
                if(spanEq(kS,kO,kL,L_RATES)){
                    skipWs();
                    if(p<n&&b[p]=='{'){
                        p++;
                        while(p<n){
                            skipWs(); if(p>=n)break;
                            if(b[p]=='}'){p++;break;}
                            if(b[p]==','){p++;continue;}
                            parseString(); byte[] cs=sSrc; int co=sOff,cl=sLen;
                            skipWs(); if(p<n&&b[p]==':')p++;
                            long rate=parseIntValue();
                            if(rCount==rSrc.length){ rSrc=Arrays.copyOf(rSrc,rSrc.length*2); rOff=Arrays.copyOf(rOff,rOff.length*2); rLen=Arrays.copyOf(rLen,rLen.length*2); rVal=Arrays.copyOf(rVal,rVal.length*2); }
                            rSrc[rCount]=cs; rOff[rCount]=co; rLen[rCount]=cl; rVal[rCount]=rate; rCount++;
                        }
                    } else skipValue();
                } else skipValue();
            }
        }

        long counted=0,totalNet=0;
        // temp holders for current txn strings: need copy of span refs because parseString overwrites statics and arena may relocate
        // account/channel spans: store src/off/len in locals immediately after parse
        while(true){
            while(p<n && (b[p]=='\n'||b[p]=='\r'||b[p]==' '||b[p]=='\t')) p++;
            if(p>=n) break;
            if(b[p]!='{'){ while(p<n && b[p]!='\n') p++; continue; }
            p++;
            byte[] aSrc=null; int aOff=0,aLen=0;
            byte[] chSrc=null; int chOff=0,chLen=0;
            long hundredths=0, rate=1000000; int sign=1; boolean skip=false;
            while(p<n){
                skipWs(); if(p>=n)break;
                byte c=b[p];
                if(c=='}'){p++;break;}
                if(c==','){p++;continue;}
                parseString();
                // copy key span
                byte[] kS=sSrc; int kO=sOff,kL=sLen;
                // determine key id without keeping refs (compare now)
                int kid=-1;
                if(kL==7 && spanEq(kS,kO,kL,L_ACCOUNT)) kid=0;
                else if(kL==4 && spanEq(kS,kO,kL,L_TYPE)) kid=1;
                else if(kL==6 && spanEq(kS,kO,kL,L_AMOUNT)) kid=2;
                else if(kL==8 && spanEq(kS,kO,kL,L_CURRENCY)) kid=3;
                else if(kL==4 && spanEq(kS,kO,kL,L_TAGS)) kid=4;
                else if(kL==4 && spanEq(kS,kO,kL,L_META)) kid=5;
                skipWs(); if(p<n&&b[p]==':')p++; skipWs();
                switch(kid){
                    case 0: if(p<n&&b[p]=='"'){ parseString(); aSrc=sSrc;aOff=sOff;aLen=sLen; } else skipValue(); break;
                    case 1: if(p<n&&b[p]=='"'){ parseString(); if(spanEq(L_VOID)) skip=true; else if(spanEq(L_DEBIT)) sign=-1; else sign=1; } else skipValue(); break;
                    case 2: if(p<n&&b[p]=='"'){ parseString(); hundredths=parseAmount(sSrc,sOff,sLen); } else skipValue(); break;
                    case 3: if(p<n&&b[p]=='"'){ parseString(); rate=0; for(int i=0;i<rCount;i++) if(rLen[i]==sLen){ boolean eq=true; for(int j=0;j<sLen;j++) if(rSrc[i][rOff[i]+j]!=sSrc[sOff+j]){eq=false;break;} if(eq){rate=rVal[i];break;} } } else skipValue(); break;
                    case 4: {
                        skipWs();
                        if(p<n&&b[p]=='['){
                            p++;
                            while(p<n){
                                skipWs(); if(p>=n)break;
                                if(b[p]==']'){p++;break;}
                                if(b[p]==','){p++;continue;}
                                if(b[p]=='"'){ parseString(); if(spanEq(L_TEST)) skip=true; } else skipValue();
                                if(skip) break;
                            }
                        } else skipValue();
                        break;
                    }
                    case 5: {
                        skipWs();
                        if(p<n&&b[p]=='{'){
                            p++;
                            while(p<n){
                                skipWs(); if(p>=n)break;
                                if(b[p]=='}'){p++;break;}
                                if(b[p]==','){p++;continue;}
                                parseString(); byte[] mS=sSrc; int mO=sOff,mL=sLen; boolean isCh = spanEq(mS,mO,mL,L_CHANNEL);
                                skipWs(); if(p<n&&b[p]==':')p++; skipWs();
                                if(isCh){ if(p<n&&b[p]=='"'){ parseString(); chSrc=sSrc;chOff=sOff;chLen=sLen; } else skipValue(); }
                                else skipValue();
                            }
                        } else skipValue();
                        break;
                    }
                    default: skipValue(); break;
                }
                if(skip){ while(p<n && b[p]!='\n') p++; if(p<n) p++; break; }
            }
            if(skip) continue;
            long usd = (hundredths * rate) / 1000000L;
            long signed = sign * usd;
            counted++; totalNet += signed;
            if(chSrc!=null){
                int idx=-1;
                for(int i=0;i<cCount;i++) if(cLen[i]==chLen){ boolean eq=true; for(int j=0;j<chLen;j++) if(cSrc[i][cOff[i]+j]!=chSrc[chOff+j]){eq=false;break;} if(eq){idx=i;break;} }
                if(idx<0){
                    if(cCount==cSrc.length){ cSrc=Arrays.copyOf(cSrc,cSrc.length*2); cOff=Arrays.copyOf(cOff,cOff.length*2); cLen=Arrays.copyOf(cLen,cLen.length*2); cCnt=Arrays.copyOf(cCnt,cCnt.length*2); cNet=Arrays.copyOf(cNet,cNet.length*2); }
                    idx=cCount++; cSrc[idx]=chSrc; cOff[idx]=chOff; cLen[idx]=chLen;
                }
                cCnt[idx]++; cNet[idx]+=signed;
            }
            if(aSrc!=null) tableAdd(aSrc,aOff,aLen,signed);
        }

        // sort channels by name byte order
        Integer[] cIdx=new Integer[cCount]; for(int i=0;i<cCount;i++)cIdx[i]=i;
        final byte[][] fcS=cSrc; final int[] fcO=cOff, fcL=cLen;
        Arrays.sort(cIdx,(x,y)->{
            int l=Math.min(fcL[x],fcL[y]);
            for(int i=0;i<l;i++){ int d=(fcS[x][fcO[x]+i]&0xff)-(fcS[y][fcO[y]+i]&0xff); if(d!=0) return d; }
            return fcL[x]-fcL[y];
        });
        // accounts top10
        int sz=tSize;
        // collect
        byte[][] aSrcA=new byte[sz][]; int[] aOffA=new int[sz],aLenA=new int[sz]; long[] aValA=new long[sz];
        int ai=0;
        for(int i=0;i<tSrc.length;i++) if(tUsed[i]){ aSrcA[ai]=tSrc[i]; aOffA[ai]=tOff[i]; aLenA[ai]=tLen[i]; aValA[ai]=tVal[i]; ai++; }
        Integer[] aIdx=new Integer[sz]; for(int i=0;i<sz;i++)aIdx[i]=i;
        Arrays.sort(aIdx,(x,y)->{
            if(aValA[x]!=aValA[y]) return aValA[x]>aValA[y]?-1:1;
            int l=Math.min(aLenA[x],aLenA[y]);
            for(int i=0;i<l;i++){ int d=(aSrcA[x][aOffA[x]+i]&0xff)-(aSrcA[y][aOffA[y]+i]&0xff); if(d!=0) return d; }
            return aLenA[x]-aLenA[y];
        });
        StringBuilder sb=new StringBuilder(4096);
        sb.append("counted ").append(counted).append('\n');
        sb.append("net ").append(totalNet).append('\n');
        for(int ii=0;ii<cCount;ii++){ int i=cIdx[ii]; sb.append("channel "); sb.append(new String(cSrc[i],cOff[i],cLen[i], java.nio.charset.StandardCharsets.UTF_8)); sb.append(' ').append(cCnt[i]).append(' ').append(cNet[i]).append('\n'); }
        int top=Math.min(10,sz);
        for(int ii=0;ii<top;ii++){ int i=aIdx[ii]; sb.append("account "); sb.append(new String(aSrcA[i],aOffA[i],aLenA[i], java.nio.charset.StandardCharsets.UTF_8)); sb.append(' ').append(aValA[i]).append('\n'); }
        // write as bytes to avoid encoding issues for raw bytes: use stdout write of UTF-8 of sb — accounts ASCII so fine
        System.out.write(sb.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
        System.out.flush();
    }
}
