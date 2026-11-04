package main
import (
 "bufio"
 "encoding/json"
 "fmt"
 "io"
 "os"
 "sort"
)
type transaction struct { Account string `json:"account"`; Type string `json:"type"`; Amount string `json:"amount"`; Currency string `json:"currency"`; Tags []string `json:"tags"`; Meta struct { Channel string `json:"channel"` } `json:"meta"` }
type stat struct { count, net int64 }
type account struct { name string; net int64 }
func amount(s string) int64 { var n int64; i:=0; for i<len(s)&&s[i]!='.' { n=n*10+int64(s[i]-'0'); i++ }; n*=100; if i<len(s) {i++; n+=int64(s[i]-'0')*10; i++; if i<len(s) {n+=int64(s[i]-'0')} }; return n }
func main() {
 f,err:=os.Open(os.Args[1]); if err!=nil { panic(err) }; defer f.Close()
 r:=bufio.NewReaderSize(f,1<<20); line,err:=r.ReadBytes('\n'); if err!=nil {panic(err)}
 var first map[string]json.RawMessage; if err=json.Unmarshal(line,&first); err!=nil {panic(err)}; rates:=make(map[string]int64); if err=json.Unmarshal(first["rates"],&rates); err!=nil {panic(err)}
 accounts:=make(map[string]int64); channels:=make(map[string]*stat); var count,net int64
 for { line,err=r.ReadBytes('\n'); if err==io.EOF && len(line)==0 {break}; if err!=nil && err!=io.EOF {panic(err)}
  var fields map[string]json.RawMessage; if e:=json.Unmarshal(line,&fields); e!=nil {panic(e)}
  var t transaction
  for _, field:=range []struct{key string; dest any}{{"account",&t.Account},{"type",&t.Type},{"amount",&t.Amount},{"currency",&t.Currency},{"tags",&t.Tags}} {if e:=json.Unmarshal(fields[field.key],field.dest); e!=nil {panic(e)}}
  var meta map[string]json.RawMessage; if e:=json.Unmarshal(fields["meta"],&meta); e!=nil {panic(e)}; if e:=json.Unmarshal(meta["channel"],&t.Meta.Channel); e!=nil {panic(e)}
  skip:=t.Type=="void"; for _,tag:=range t.Tags { if tag=="test" {skip=true; break} }; if skip {continue}
  rate:=rates[t.Currency]; var product int64; if rate!=0 {product=amount(t.Amount)*rate}; value:=product/1000000; if product<0 && product%1000000!=0 {value--}; if t.Type=="debit" {value=-value}; count++; net+=value; accounts[t.Account]+=value
  s:=channels[t.Meta.Channel]; if s==nil {s=&stat{}; channels[t.Meta.Channel]=s}; s.count++; s.net+=value
 }
 w:=bufio.NewWriter(os.Stdout); defer w.Flush(); fmt.Fprintf(w,"counted %d\nnet %d\n",count,net)
 names:=make([]string,0,len(channels)); for name:=range channels {names=append(names,name)}; sort.Strings(names)
 for _,name:=range names {s:=channels[name]; fmt.Fprintf(w,"channel %s %d %d\n",name,s.count,s.net)}
 list:=make([]account,0,len(accounts)); for name,n:=range accounts {list=append(list,account{name,n})}; sort.Slice(list,func(i,j int)bool {if list[i].net!=list[j].net {return list[i].net>list[j].net}; return list[i].name<list[j].name})
 for i:=0;i<len(list)&&i<10;i++ {fmt.Fprintf(w,"account %s %d\n",list[i].name,list[i].net)}
}
