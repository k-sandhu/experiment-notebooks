package main
import ("fmt"; "os"; "bufio"; "strconv"; "sync")
type result struct { spread, bumps, returns, id, distance int64 }
func main() {
 f,_:=os.Open(os.Args[1]); defer f.Close(); var n,steps,b int64; var seed uint64; fmt.Fscan(bufio.NewReader(f),&n,&steps,&b,&seed)
 workers,_:=strconv.Atoi(os.Args[2]); results:=make([]result,workers); var wg sync.WaitGroup; wg.Add(workers)
 for k:=0;k<workers;k++ { go func(i int) { defer wg.Done(); a:=result{distance:-1}; w:=int64(workers); ii:=int64(i); rem:=n%w; start:=n/w*ii; end:=n/w*(ii+1); if ii<rem {start+=ii} else {start+=rem}; if ii+1<rem {end+=ii+1} else {end+=rem}
  for j:=start;j<end;j++ {state:=seed+uint64(j); var x,y int64
   for s:=int64(0);s<steps;s++ {state+=0x9E3779B97F4A7C15; z:=state; z=(z^(z>>30))*0xBF58476D1CE4E5B9; z=(z^(z>>27))*0x94D049BB133111EB
    switch z>>62 {case 0: if x<b {x++} else {a.bumps++;continue}; case 1: if x> -b {x--} else {a.bumps++;continue}; case 2: if y<b {y++} else {a.bumps++;continue}; default: if y> -b {y--} else {a.bumps++;continue}}
    if x==0 && y==0 {a.returns++}
   }
   a.spread+=x*x+y*y; xx,yy:=x,y; if xx<0 {xx= -xx}; if yy<0 {yy= -yy}; d:=xx+yy; if d>a.distance {a.distance=d;a.id=j}
  }; results[i]=a
 }(k) }; wg.Wait(); all:=result{distance:-1}; for _,a:=range results {all.spread+=a.spread;all.bumps+=a.bumps;all.returns+=a.returns; if a.distance>all.distance || (a.distance==all.distance && a.id<all.id) {all.distance=a.distance;all.id=a.id}}
 fmt.Printf("spread %d\nbumps %d\nreturns %d\nfarthest %d %d\n",all.spread,all.bumps,all.returns,all.id,all.distance)
}
