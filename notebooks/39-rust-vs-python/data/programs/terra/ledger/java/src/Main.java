import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import com.fasterxml.jackson.core.*;

public class Main {
    static final JsonFactory factory = new JsonFactory();
    static class Stat { long count, net; }
    static long amount(String s) {
        long n=0; int i=0;
        while(i<s.length() && s.charAt(i)!='.') n=n*10+s.charAt(i++)-'0';
        n*=100; if(i<s.length()) { i++; n+=(s.charAt(i++)-'0')*10; if(i<s.length()) n+=s.charAt(i)-'0'; }
        return n;
    }
    public static void main(String[] args) throws Exception {
        Map<String,Long> rates=new HashMap<>(), accounts=new HashMap<>(); Map<String,Stat> channels=new HashMap<>();
        long count=0, net=0;
        try (BufferedReader in=new BufferedReader(new InputStreamReader(new FileInputStream(args[0]),StandardCharsets.UTF_8), 1<<20)) {
            try(JsonParser p=factory.createParser(in.readLine())) {
                p.nextToken(); while(p.nextToken()!=JsonToken.END_OBJECT) { String k=p.currentName(); p.nextToken();
                    if(k.equals("rates")) { while(p.nextToken()!=JsonToken.END_OBJECT) { String c=p.currentName(); p.nextToken(); rates.put(c,p.getLongValue()); } } else p.skipChildren();
                }
            }
            String line; while((line=in.readLine())!=null) {
                String account=null,type=null,currency=null,channel=null,amt=null; boolean skip=false;
                try(JsonParser p=factory.createParser(line)) {
                    p.nextToken(); while(p.nextToken()!=JsonToken.END_OBJECT) {
                        String k=p.currentName(); p.nextToken();
                        switch(k) {
                            case "account": account=p.getText(); break;
                            case "type": type=p.getText(); break;
                            case "currency": currency=p.getText(); break;
                            case "amount": amt=p.getText(); break;
                            case "tags": while(p.nextToken()!=JsonToken.END_ARRAY) if(p.getText().equals("test")) skip=true; break;
                            case "meta": while(p.nextToken()!=JsonToken.END_OBJECT) { String m=p.currentName(); p.nextToken(); if(m.equals("channel")) channel=p.getText(); else p.skipChildren(); } break;
                            default: p.skipChildren();
                        }
                    }
                }
                if(skip || type.equals("void")) continue;
                long rate=rates.get(currency); long product=rate==0?0:amount(amt)*rate; long value=Math.floorDiv(product,1000000L); if(type.equals("debit")) value=-value;
                count++; net+=value; accounts.merge(account,value,Long::sum);
                Stat s=channels.computeIfAbsent(channel,k->new Stat()); s.count++; s.net+=value;
            }
        }
        StringBuilder out=new StringBuilder().append("counted ").append(count).append("\nnet ").append(net).append('\n');
        ArrayList<String> names=new ArrayList<>(channels.keySet()); Collections.sort(names);
        for(String name:names) { Stat s=channels.get(name); out.append("channel ").append(name).append(' ').append(s.count).append(' ').append(s.net).append('\n'); }
        ArrayList<Map.Entry<String,Long>> list=new ArrayList<>(accounts.entrySet());
        list.sort((a,b)->{int c=Long.compare(b.getValue(),a.getValue()); return c!=0?c:a.getKey().compareTo(b.getKey());});
        for(int i=0;i<Math.min(10,list.size());i++) { var e=list.get(i); out.append("account ").append(e.getKey()).append(' ').append(e.getValue()).append('\n'); }
        System.out.print(out);
    }
}
