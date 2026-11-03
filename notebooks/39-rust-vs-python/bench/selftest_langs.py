"""Small independent heat implementations for language harness checks."""

CPP = r'''
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
using namespace std;
int main(int argc,char**argv){ifstream f(argv[1]); int h,w,s;f>>h>>w>>s;vector<string> g(h);for(auto &r:g)f>>r;vector<long long> a(h*w),b;for(int i=0;i<h*w;i++)if(isdigit(g[i/w][i%w]))a[i]=(g[i/w][i%w]-'0')*1000;for(int t=0;t<s;t++){b=a;for(int i=0;i<h*w;i++){int r=i/w,c=i%w;if(g[r][c]!='.')continue;long long x=4*a[i];for(auto [dr,dc]:vector<pair<int,int>>{{-1,0},{1,0},{0,-1},{0,1}}){int y=r+dr,z=c+dc;x+=(y<0||y>=h||z<0||z>=w||g[y][z]=='#')?a[i]:a[y*w+z];}b[i]=x/8;}a=b;}long long sum=0,check=0,m=-1;int at=0;for(int i=0;i<h*w;i++)if(g[i/w][i%w]=='.'){sum+=a[i];check+=a[i]*(i+1);if(a[i]>m)m=a[i],at=i;}cout<<"sum "<<sum<<"\nmax "<<m<<" "<<at/w<<" "<<at%w<<"\nchecksum "<<check<<"\n";}
'''
JAVA = r'''
import java.nio.file.*; import com.fasterxml.jackson.core.JsonFactory;
public class Main { public static void main(String[] a) throws Exception { new JsonFactory(); String[] lines=Files.readString(Path.of(a[0])).strip().split("\\R"); String[] d=lines[0].split(" "); int h=Integer.parseInt(d[0]),w=Integer.parseInt(d[1]),s=Integer.parseInt(d[2]); long[] v=new long[h*w]; for(int i=0;i<h*w;i++){char c=lines[1+i/w].charAt(i%w);if(Character.isDigit(c))v[i]=(c-'0')*1000;} int[] dr={-1,1,0,0},dc={0,0,-1,1};for(int t=0;t<s;t++){long[] n=v.clone();for(int i=0;i<h*w;i++){int r=i/w,c=i%w;if(lines[r+1].charAt(c)!='.')continue;long x=4*v[i];for(int k=0;k<4;k++){int y=r+dr[k],z=c+dc[k];x+=(y<0||y>=h||z<0||z>=w||lines[y+1].charAt(z)=='#')?v[i]:v[y*w+z];}n[i]=x/8;}v=n;}long sum=0,check=0,m=-1;int at=0;for(int i=0;i<h*w;i++)if(lines[i/w+1].charAt(i%w)=='.'){sum+=v[i];check+=v[i]*(i+1);if(v[i]>m){m=v[i];at=i;}}System.out.printf("sum %d\nmax %d %d %d\nchecksum %d\n",sum,m,at/w,at%w,check);}}
'''
CSHARP = r'''
using System; using System.IO;
class Program { static void Main(string[] args) { var lines=File.ReadAllLines(args[0]);var d=lines[0].Split(' ');int h=int.Parse(d[0]),w=int.Parse(d[1]),s=int.Parse(d[2]);long[] v=new long[h*w];for(int i=0;i<h*w;i++){char c=lines[1+i/w][i%w];if(char.IsDigit(c))v[i]=(c-'0')*1000;}int[] dr={-1,1,0,0},dc={0,0,-1,1};for(int t=0;t<s;t++){var n=(long[])v.Clone();for(int i=0;i<h*w;i++){int r=i/w,c=i%w;if(lines[r+1][c]!='.')continue;long x=4*v[i];for(int k=0;k<4;k++){int y=r+dr[k],z=c+dc[k];x+=(y<0||y>=h||z<0||z>=w||lines[y+1][z]=='#')?v[i]:v[y*w+z];}n[i]=x/8;}v=n;}long sum=0,check=0,m=-1;int at=0;for(int i=0;i<h*w;i++)if(lines[i/w+1][i%w]=='.'){sum+=v[i];check+=v[i]*(i+1);if(v[i]>m){m=v[i];at=i;}}Console.WriteLine($"sum {sum}\nmax {m} {at/w} {at%w}\nchecksum {check}");}}
'''
GO = r'''
package main
import("fmt";"os";"strings";"strconv")
func main(){b,_:=os.ReadFile(os.Args[1]);l:=strings.Split(strings.TrimSpace(string(b)),"\n");d:=strings.Fields(l[0]);h,_:=strconv.Atoi(d[0]);w,_:=strconv.Atoi(d[1]);s,_:=strconv.Atoi(d[2]);v:=make([]int64,h*w);for i:=range v {c:=l[i/w+1][i%w];if c>='0'&&c<='9'{v[i]=int64(c-'0')*1000}};dr:=[]int{-1,1,0,0};dc:=[]int{0,0,-1,1};for t:=0;t<s;t++{n:=append([]int64(nil),v...);for i:=range v{r,c:=i/w,i%w;if l[r+1][c]!='.'{continue};x:=4*v[i];for k:=0;k<4;k++{y,z:=r+dr[k],c+dc[k];if y<0||y>=h||z<0||z>=w||l[y+1][z]=='#'{x+=v[i]}else{x+=v[y*w+z]}};n[i]=x/8};v=n};var sum,check int64; m:=int64(-1);at:=0;for i:=range v{if l[i/w+1][i%w]=='.'{sum+=v[i];check+=v[i]*int64(i+1);if v[i]>m{m=v[i];at=i}}};fmt.Printf("sum %d\nmax %d %d %d\nchecksum %d\n",sum,m,at/w,at%w,check)}
'''
JS = r'''
const l=require("fs").readFileSync(process.argv[2],"utf8").trim().split(/\r?\n/),[h,w,s]=l[0].split(" ").map(Number);let v=Array(h*w).fill(0);for(let i=0;i<v.length;i++){let c=l[1+Math.floor(i/w)][i%w];if(c>='0'&&c<='9')v[i]=Number(c)*1000}for(let t=0;t<s;t++){let n=v.slice();for(let i=0;i<v.length;i++){let r=Math.floor(i/w),c=i%w;if(l[r+1][c]!='.')continue;let x=4*v[i];for(let [dr,dc] of [[-1,0],[1,0],[0,-1],[0,1]]){let y=r+dr,z=c+dc;x+=(y<0||y>=h||z<0||z>=w||l[y+1][z]=='#')?v[i]:v[y*w+z]}n[i]=Math.floor(x/8)}v=n}let sum=0,check=0,m=-1,at=0;for(let i=0;i<v.length;i++)if(l[1+Math.floor(i/w)][i%w]=='.'){sum+=v[i];check+=v[i]*(i+1);if(v[i]>m){m=v[i];at=i}}console.log(`sum ${sum}\nmax ${m} ${Math.floor(at/w)} ${at%w}\nchecksum ${check}`);
'''
