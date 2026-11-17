using System.Text;
using System.Text.Json;
using System.Globalization;

class Stat { public long Count, Net; }
class Program {
    static long Amount(string s) {
        long n=0; int i=0;
        while(i<s.Length && s[i]!='.') n=n*10+s[i++]-'0';
        n*=100; if(i<s.Length) { i++; n+=(s[i++]-'0')*10; if(i<s.Length) n+=s[i]-'0'; }
        return n;
    }
    static void Main(string[] args) {
        var rates=new Dictionary<string,long>(); var accounts=new Dictionary<string,long>(); var channels=new Dictionary<string,Stat>();
        long count=0, net=0;
        using var input=new StreamReader(args[0],Encoding.UTF8, true, 1<<20);
        using(var first=JsonDocument.Parse(input.ReadLine())) foreach(var r in first.RootElement.GetProperty("rates").EnumerateObject()) rates[r.Name]=r.Value.GetInt64();
        string line;
        while((line=input.ReadLine())!=null) {
            using var doc=JsonDocument.Parse(line); var j=doc.RootElement;
            string type=j.GetProperty("type").GetString(); if(type=="void") continue;
            bool skip=false; foreach(var tag in j.GetProperty("tags").EnumerateArray()) if(tag.ValueEquals("test")) { skip=true; break; }
            if(skip) continue;
            long rate=rates[j.GetProperty("currency").GetString()]; long product=rate==0?0:Amount(j.GetProperty("amount").GetString())*rate;
            long value=product/1000000; if(product<0 && product%1000000!=0) value--;
            if(type=="debit") value=-value; count++; net+=value;
            string account=j.GetProperty("account").GetString(); accounts.TryGetValue(account,out long old); accounts[account]=old+value;
            string channel=j.GetProperty("meta").GetProperty("channel").GetString();
            if(!channels.TryGetValue(channel,out var stat)) channels[channel]=stat=new Stat(); stat.Count++; stat.Net+=value;
        }
        var output=new StringBuilder(); output.Append("counted ").Append(count.ToString(CultureInfo.InvariantCulture)).Append("\nnet ").Append(net.ToString(CultureInfo.InvariantCulture)).Append('\n');
        foreach(var item in channels.OrderBy(x=>x.Key,StringComparer.Ordinal)) output.Append("channel ").Append(item.Key).Append(' ').Append(item.Value.Count.ToString(CultureInfo.InvariantCulture)).Append(' ').Append(item.Value.Net.ToString(CultureInfo.InvariantCulture)).Append('\n');
        foreach(var item in accounts.OrderByDescending(x=>x.Value).ThenBy(x=>x.Key,StringComparer.Ordinal).Take(10)) output.Append("account ").Append(item.Key).Append(' ').Append(item.Value.ToString(CultureInfo.InvariantCulture)).Append('\n');
        Console.Write(output.ToString());
    }
}
