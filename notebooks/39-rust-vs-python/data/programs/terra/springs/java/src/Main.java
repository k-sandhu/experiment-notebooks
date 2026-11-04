import java.nio.file.*;
import java.util.Locale;
public class Main {
    static class Input { String s; int p; Input(String path) throws Exception { s=Files.readString(Path.of(path)); } double next(){int n=s.length(); while(p<n && s.charAt(p)<=32)p++; int b=p; while(p<n && s.charAt(p)>32)p++; return Double.parseDouble(s.substring(b,p));} }
    public static void main(String[] args) throws Exception {
        Input in=new Input(args[0]); int n=(int)in.next(), steps=(int)in.next(); double dt=in.next(), P=in.next();
        double[] x=new double[n],v=new double[n],m=new double[n],k=new double[n],r=new double[n],c=new double[n],f=new double[n];
        for(int i=0;i<n;i++){x[i]=in.next();v[i]=in.next();m[i]=in.next();k[i]=in.next();r[i]=in.next();c[i]=in.next();}
        for(int t=0;t<steps;t++){
            for(int i=0;i<n-1;i++) f[i]=k[i]*((x[i+1]-x[i])-r[i]);
            f[n-1]=k[n-1]*(((x[0]+P)-x[n-1])-r[n-1]);
            double prev=f[n-1];
            for(int i=0;i<n;i++){double force=(f[i]-prev)-(c[i]*v[i]);prev=f[i];v[i]=v[i]+dt*(force/m[i]);x[i]=x[i]+dt*v[i];}
        }
        double K=0,U=0,X=0,best=-1;int j=0;
        for(int i=0;i<n;i++){K+=((0.5*m[i])*v[i])*v[i];X+=x[i];double a=Math.abs(v[i]);if(a>best){best=a;j=i;}double s=(i==n-1?((x[0]+P)-x[i]):(x[i+1]-x[i]))-r[i];U+=((0.5*k[i])*s)*s;}
        System.out.printf(Locale.ROOT,"kinetic %.17g%npotential %.17g%nposition %.17g%nfastest %d%n",K,U,X,j);
    }
}
