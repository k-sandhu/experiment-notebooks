import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.regex.*;
public class Main {
 static final Pattern LINE=Pattern.compile("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\\.[0-9]{3}Z [a-z]+-[0-9]+ (?:GET|POST|PUT|DELETE|PATCH) (/[A-Za-z0-9_/-]*)(?:\\?[^ ]*)? ([0-9])[0-9]{2} [0-9]+B ([0-9]+)\\.([0-9])ms \"[^\"]*\"");
 static String template(String s){StringBuilder b=new StringBuilder(s.length()); int i=0; while(i<s.length()){b.append('/');int start=++i; boolean numeric=true; while(i<s.length()&&s.charAt(i)!='/'){char c=s.charAt(i++);if(c<'0'||c>'9')numeric=false;} if(i>start&&numeric)b.append("{id}");else b.append(s,start,i);}return b.toString();}
 static String number(String whole,String frac){int i=0;while(i<whole.length()&&whole.charAt(i)=='0')i++;String s=whole.substring(i)+frac;return s;}
 static String fmt(String s){return s.length()==1?"0."+s:s.substring(0,s.length()-1)+"."+s.charAt(s.length()-1);}
 public static void main(String[] args)throws Exception {Map<String,ArrayList<String>> paths=new HashMap<>(); long[] statuses=new long[10];long lines=0,bad=0;
 try(BufferedReader r=new BufferedReader(new InputStreamReader(new FileInputStream(args[0]),StandardCharsets.US_ASCII), 1<<20)){String line;Matcher m=LINE.matcher("");while((line=r.readLine())!=null){lines++;m.reset(line);if(!m.matches()){bad++;continue;}String p=template(m.group(1));paths.computeIfAbsent(p,k->new ArrayList<>()).add(number(m.group(3),m.group(4)));statuses[m.group(2).charAt(0)-'0']++;}}
 StringBuilder out=new StringBuilder().append("lines ").append(lines).append("\nmalformed ").append(bad).append('\n');for(int i=0;i<10;i++)if(statuses[i]!=0)out.append("status ").append(i).append("xx ").append(statuses[i]).append('\n');
 var top=new ArrayList<>(paths.entrySet());top.sort((a,b)->{int c=Integer.compare(b.getValue().size(),a.getValue().size());return c!=0?c:a.getKey().compareTo(b.getKey());});
 for(int i=0;i<Math.min(10,top.size());i++){var e=top.get(i);var v=e.getValue();v.sort((a,b)->{int c=Integer.compare(a.length(),b.length());return c!=0?c:a.compareTo(b);});int n=v.size();out.append("path ").append(e.getKey()).append(' ').append(n).append(' ').append(fmt(v.get((n-1)/2))).append(' ').append(fmt(v.get(n-n/20-1))).append(' ').append(fmt(v.get(n-1))).append('\n');}System.out.print(out);
 }
}
