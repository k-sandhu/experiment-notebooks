package main
import("bufio";"fmt";"os";"sort")
type table struct { keys, counts []uint64; used int }
func hash(x uint64) uint64 { x^=x>>30; x*=0xbf58476d1ce4e5b9; x^=x>>27; x*=0x94d049bb133111eb; return x^(x>>31) }
func (t *table) grow(){ oldk,oldc:=t.keys,t.counts; n:=len(oldk)*2; t.keys=make([]uint64,n);t.counts=make([]uint64,n);for i,k:=range oldk {if k!=0 {p:=int(hash(k)&uint64(n-1));for t.keys[p]!=0 {p=(p+1)&(n-1)};t.keys[p]=k;t.counts[p]=oldc[i]}} }
func(t *table)add(k uint64){if (t.used+1)*10>=len(t.keys)*7 {t.grow()};m:=len(t.keys)-1;p:=int(hash(k)&uint64(m));for t.keys[p]!=0&&t.keys[p]!=k {p=(p+1)&m};if t.keys[p]==0 {t.keys[p]=k;t.used++};t.counts[p]++}
type row struct{k,c uint64}
func main(){if len(os.Args)<2{return}; b,e:=os.ReadFile(os.Args[1]);if e!=nil{fmt.Fprintln(os.Stderr,e);os.Exit(1)};for i,c:=range b {if c>='A'&&c<='Z'{b[i]=c+32}}; ids:=make(map[string]uint32); words:=[]string{""}; t:=table{keys:make([]uint64,1024),counts:make([]uint64,1024)};var total,pairs uint64;var prev uint32
 for i:=0;i<len(b); {c:=b[i];if c>='a'&&c<='z'{start:=i;i++;for i<len(b)&&b[i]>='a'&&b[i]<='z'{i++};id,ok:=ids[string(b[start:i])];if !ok{w:=string(b[start:i]);id=uint32(len(words));ids[w]=id;words=append(words,w)};total++;if prev!=0{t.add(uint64(prev)<<32|uint64(id));pairs++};prev=id}else{if c=='.'||c=='!'||c=='?'{prev=0};i++}}
 top:=make([]row,0,21);better:=func(a,b row)bool{if a.c!=b.c{return a.c>b.c};af,bf:=words[uint32(a.k>>32)],words[uint32(b.k>>32)];if af!=bf{return af<bf};return words[uint32(a.k)]<words[uint32(b.k)]};for i,k:=range t.keys{if k!=0&&(len(top)<20||t.counts[i]>=top[len(top)-1].c){r:=row{k,t.counts[i]};p:=sort.Search(len(top),func(j int)bool{return !better(top[j],r)});if p<20 {top=append(top,row{});copy(top[p+1:],top[p:]);top[p]=r;if len(top)>20{top=top[:20]}}}}
 out:=bufio.NewWriter(os.Stdout);fmt.Fprintf(out,"words %d\npairs %d\ndistinct %d\n",total,pairs,t.used);for _,r:=range top{fmt.Fprintf(out,"%d %s %s\n",r.c,words[uint32(r.k>>32)],words[uint32(r.k)])};out.Flush()}
