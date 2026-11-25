import java.io.*;
import java.nio.file.*;
import java.util.*;

public class Main {
    static boolean isDig(byte c){ return c>='0' && c<='9'; }
    static boolean isLow(byte c){ return c>='a' && c<='z'; }
    static boolean isPathCh(byte c){
        return (c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='/'||c=='-';
    }
    static int indexOfByte(byte[] a, int from, int to, byte v){
        for(int i=from;i<to;i++) if(a[i]==v) return i;
        return -1;
    }
    static int indexOfByte(byte[] a, int from, byte v){
        // manual loop; Arrays? use loop over length
        for(int i=from;i<a.length;i++) if(a[i]==v) return i;
        return -1;
    }

    static final class Entry {
        byte[] key;
        int[] lats = new int[16];
        int size;
        int mx;
        void add(int v){
            if(size==lats.length) lats = Arrays.copyOf(lats, lats.length*2);
            lats[size++]=v;
            if(v>mx) mx=v;
        }
    }

    public static void main(String[] args) throws Exception {
        if(args.length<1) System.exit(1);
        byte[] data = Files.readAllBytes(Path.of(args[0]));
        long total=0, malformed=0;
        long[] statusCnt = new long[10];

        ArrayList<Entry> entries = new ArrayList<>(1024);
        int tcap = 1024;
        int[] slots = new int[tcap];
        int usedSlots=0;

        byte[] tmp = new byte[256];

        int n=data.length;
        int pos=0;
        while(pos<n){
            int lineStart=pos;
            int nl = indexOfByte(data, pos, (byte)'\n');
            int lineEnd;
            if(nl>=0){ lineEnd=nl; pos=nl+1; } else { lineEnd=n; pos=n; }
            total++;
            int ln = lineEnd-lineStart;
            // s accessed as data[lineStart + idx]
            boolean ok=true;
            int statusClass=0;
            int latency=0;
            int pathStart=0, pathEnd=0;

            if(ln<25) ok=false;
            else {
                byte[] d=data; int b=lineStart;
                if(!(isDig(d[b])&&isDig(d[b+1])&&isDig(d[b+2])&&isDig(d[b+3])&&d[b+4]=='-'&&isDig(d[b+5])&&isDig(d[b+6])&&d[b+7]=='-'&&isDig(d[b+8])&&isDig(d[b+9])&&d[b+10]=='T'&&isDig(d[b+11])&&isDig(d[b+12])&&d[b+13]==':'&&isDig(d[b+14])&&isDig(d[b+15])&&d[b+16]==':'&&isDig(d[b+17])&&isDig(d[b+18])&&d[b+19]=='.'&&isDig(d[b+20])&&isDig(d[b+21])&&isDig(d[b+22])&&d[b+23]=='Z'&&d[b+24]==' ')) ok=false;
                else {
                    int i=25;
                    int st=i;
                    while(i<ln && isLow(d[b+i])) i++;
                    if(i==st) ok=false;
                    else if(i>=ln || d[b+i]!='-') ok=false;
                    else {
                        i++; st=i;
                        while(i<ln && isDig(d[b+i])) i++;
                        if(i==st || i>=ln || d[b+i]!=' ') ok=false;
                        else {
                            i++;
                            // method
                            int rem=ln-i;
                            if(rem>=4 && d[b+i]=='G'&&d[b+i+1]=='E'&&d[b+i+2]=='T'&&d[b+i+3]==' ') i+=4;
                            else if(rem>=4 && d[b+i]=='P'&&d[b+i+1]=='U'&&d[b+i+2]=='T'&&d[b+i+3]==' ') i+=4;
                            else if(rem>=5 && d[b+i]=='P'&&d[b+i+1]=='O'&&d[b+i+2]=='S'&&d[b+i+3]=='T'&&d[b+i+4]==' ') i+=5;
                            else if(rem>=6 && d[b+i]=='P'&&d[b+i+1]=='A'&&d[b+i+2]=='T'&&d[b+i+3]=='C'&&d[b+i+4]=='H'&&d[b+i+5]==' ') i+=6;
                            else if(rem>=7 && d[b+i]=='D'&&d[b+i+1]=='E'&&d[b+i+2]=='L'&&d[b+i+3]=='E'&&d[b+i+4]=='T'&&d[b+i+5]=='E'&&d[b+i+6]==' ') i+=7;
                            else ok=false;
                            if(ok){
                                if(i>=ln || d[b+i]!='/') ok=false;
                                else {
                                    pathStart=i;
                                    while(i<ln && d[b+i]!=' ' && d[b+i]!='?'){
                                        if(!isPathCh(d[b+i])){ ok=false; break; }
                                        i++;
                                    }
                                    if(ok){
                                        pathEnd=i;
                                        if(i<ln && d[b+i]=='?'){
                                            i++;
                                            while(i<ln && d[b+i]!=' ') i++;
                                        }
                                        if(i>=ln || d[b+i]!=' ') ok=false;
                                        else {
                                            i++;
                                            if(i+4>ln || !isDig(d[b+i])||!isDig(d[b+i+1])||!isDig(d[b+i+2])||d[b+i+3]!=' ') ok=false;
                                            else {
                                                statusClass=d[b+i]-'0';
                                                i+=4;
                                                st=i;
                                                while(i<ln && isDig(d[b+i])) i++;
                                                if(i==st || i>=ln || d[b+i]!='B') ok=false;
                                                else {
                                                    i++;
                                                    if(i>=ln || d[b+i]!=' ') ok=false;
                                                    else {
                                                        i++;
                                                        st=i; int v=0;
                                                        while(i<ln && isDig(d[b+i])){ v=v*10+(d[b+i]-'0'); i++; }
                                                        if(i==st || i>=ln || d[b+i]!='.') ok=false;
                                                        else {
                                                            i++;
                                                            if(i>=ln || !isDig(d[b+i])) ok=false;
                                                            else {
                                                                v=v*10+(d[b+i]-'0'); i++; latency=v;
                                                                if(i+2>ln || d[b+i]!='m' || d[b+i+1]!='s') ok=false;
                                                                else {
                                                                    i+=2;
                                                                    if(i>=ln || d[b+i]!=' ') ok=false;
                                                                    else {
                                                                        i++;
                                                                        if(i>=ln || d[b+i]!='"') ok=false;
                                                                        else if(d[b+ln-1]!='"' || i+1>=ln) ok=false;
                                                                        else if(indexOfByte(d, b+i+1, b+ln-1, (byte)'"')>=0) ok=false;
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            if(!ok){ malformed++; continue; }
            statusCnt[statusClass]++;

            // build template
            if(tmp.length < (pathEnd-pathStart)+16) tmp = new byte[(pathEnd-pathStart)+64];
            int tlen=0;
            int p=pathStart;
            int b=lineStart;
            while(true){
                int segStart=p;
                while(p<pathEnd && data[b+p]!='/') p++;
                int segLen=p-segStart;
                boolean allDig = segLen>0;
                if(allDig) for(int k=segStart;k<p;k++) if(!isDig(data[b+k])){ allDig=false; break; }
                int need = tlen + (allDig?4:segLen) + 1;
                if(need>tmp.length) tmp = Arrays.copyOf(tmp, tmp.length*2+32);
                if(allDig){ tmp[tlen++]='{'; tmp[tlen++]='i'; tmp[tlen++]='d'; tmp[tlen++]='}'; }
                else if(segLen>0){ System.arraycopy(data, b+segStart, tmp, tlen, segLen); tlen+=segLen; }
                if(p>=pathEnd) break;
                tmp[tlen++]='/';
                p++;
            }

            // hash FNV
            long h = 0xcbf29ce484222325L; // 146959... signed same bits
            // Use unsigned-like 64 overflow fine
            for(int k=0;k<tlen;k++){ h ^= (tmp[k]&0xffL); h *= 1099511628211L; }

            if((usedSlots+1)*10 > tcap*7){
                int ncap=tcap*2;
                int[] nslots=new int[ncap];
                int mask=ncap-1;
                for(int ei=0; ei<entries.size(); ei++){
                    Entry en=entries.get(ei);
                    long hh=0xcbf29ce484222325L;
                    for(byte ch: en.key){ hh ^= (ch&0xffL); hh *= 1099511628211L; }
                    int idx=(int)(hh & mask);
                    while(nslots[idx]!=0) idx=(idx+1)&mask;
                    nslots[idx]=ei+1;
                }
                slots=nslots; tcap=ncap;
            }
            int mask=tcap-1;
            int idx=(int)(h & mask);
            Entry found=null;
            int foundIdx=-1;
            while(true){
                int v=slots[idx];
                if(v==0) break;
                Entry en=entries.get(v-1);
                if(en.key.length==tlen){
                    boolean eq=true;
                    for(int k=0;k<tlen;k++) if(en.key[k]!=tmp[k]){ eq=false; break; }
                    if(eq){ found=en; foundIdx=v-1; break; }
                }
                idx=(idx+1)&mask;
            }
            if(found!=null){
                found.add(latency);
            } else {
                Entry en=new Entry();
                en.key=Arrays.copyOf(tmp, tlen);
                en.add(latency);
                entries.add(en);
                slots[idx]=entries.size();
                usedSlots++;
            }
        }

        entries.sort((a2,b2)->{
            if(a2.size!=b2.size) return Integer.compare(b2.size, a2.size);
            // byte order unsigned
            int ml=Math.min(a2.key.length,b2.key.length);
            for(int k=0;k<ml;k++){
                int x=a2.key[k]&0xff, y=b2.key[k]&0xff;
                if(x!=y) return Integer.compare(x,y);
            }
            return Integer.compare(a2.key.length,b2.key.length);
        });
        int top=Math.min(10, entries.size());
        StringBuilder out=new StringBuilder(4096);
        out.append("lines ").append(total).append('\n');
        out.append("malformed ").append(malformed).append('\n');
        for(int c=0;c<10;c++) if(statusCnt[c]>0) out.append("status ").append((char)('0'+c)).append("xx ").append(statusCnt[c]).append('\n');
        for(int ti=0; ti<top; ti++){
            Entry en=entries.get(ti);
            Arrays.sort(en.lats,0,en.size);
            long nn=en.size;
            long r50=(50*nn+99)/100;
            long r95=(95*nn+99)/100;
            int p50=en.lats[(int)(r50-1)];
            int p95=en.lats[(int)(r95-1)];
            out.append("path ");
            // decode ASCII
            for(byte ch: en.key) out.append((char)(ch&0xff));
            out.append(' ').append(nn).append(' ');
            out.append(p50/10).append('.').append(p50%10).append(' ');
            out.append(p95/10).append('.').append(p95%10).append(' ');
            out.append(en.mx/10).append('.').append(en.mx%10).append('\n');
        }
        System.out.print(out.toString());
    }
}
