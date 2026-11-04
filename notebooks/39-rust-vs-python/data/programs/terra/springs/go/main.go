package main
import ("os"; "strconv"; "strings"; "fmt"; "math")
func main(){
 data,_:=os.ReadFile(os.Args[1]); fields:=strings.Fields(string(data)); p:=0
 next:=func() float64 {v,_:=strconv.ParseFloat(fields[p],64);p++;return v}
 n,steps:=int(next()),int(next()); dt,P:=next(),next()
 x,v,m,k,r,c,f:=make([]float64,n),make([]float64,n),make([]float64,n),make([]float64,n),make([]float64,n),make([]float64,n),make([]float64,n)
 for i:=0;i<n;i++ {x[i]=next();v[i]=next();m[i]=next();k[i]=next();r[i]=next();c[i]=next()}
 for t:=0;t<steps;t++ {
  for i:=0;i<n-1;i++ {f[i]=k[i]*((x[i+1]-x[i])-r[i])}
  f[n-1]=k[n-1]*(((x[0]+P)-x[n-1])-r[n-1]); prev:=f[n-1]
  for i:=0;i<n;i++ {force:=(f[i]-prev)-float64(c[i]*v[i]);prev=f[i];v[i]=v[i]+float64(dt*(force/m[i]));x[i]=x[i]+float64(dt*v[i])}
 }
 K,U,X,best:=0.0,0.0,0.0,-1.0; j:=0
 for i:=0;i<n;i++ {K+=float64(float64(float64(0.5*m[i])*v[i])*v[i]);X+=x[i];a:=math.Abs(v[i]);if a>best {best=a;j=i};var s float64;if i==n-1{s=((x[0]+P)-x[i])-r[i]}else{s=(x[i+1]-x[i])-r[i]};U+=float64(float64(float64(0.5*k[i])*s)*s)}
 fmt.Printf("kinetic %.17g\npotential %.17g\nposition %.17g\nfastest %d\n",K,U,X,j)
}
