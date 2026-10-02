"""Two-client closed-loop benchmark; raw completion events retained for charting."""
import concurrent.futures, json, os, threading, time, urllib.request
URL=os.environ.get('BENCHMARK_URL','http://inference-gateway.agentgateway-system.svc.cluster.local:8080/benchmark/v1/chat/completions')
LABEL=os.environ.get('BENCHMARK_LABEL','unknown')
DURATION=float(os.environ.get('BENCHMARK_SECONDS','120'))
CONCURRENCY=2
OUTPUT_TOKENS=128
lock=threading.Lock(); events=[]; failures=[]; sequence=0

def request(i):
    # Distinct first text avoids reusing the entire prompt between requests.
    prompt=f'Request {i:06d}. Explain how Kubernetes schedules a pod, including resource requests, node selection, and what happens when no suitable node is available.'
    payload={'model':'qwen3-0.6b','messages':[{'role':'user','content':prompt}], 'temperature':0,'max_tokens':OUTPUT_TOKENS,'ignore_eos':True,'stream':False,'chat_template_kwargs':{'enable_thinking':False}}
    before=time.monotonic()
    with urllib.request.urlopen(urllib.request.Request(URL,json.dumps(payload).encode(),{'Content-Type':'application/json'}),timeout=180) as r:
        response=json.load(r)
    return before,time.monotonic(),response['usage']
# Warm up both execution slots before timing; model download and startup excluded.
with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
    list(pool.map(request,[-2,-1]))
started_at=time.time(); start=time.monotonic(); deadline=start+DURATION

def worker():
    global sequence
    while time.monotonic()<deadline:
        with lock:
            i=sequence;sequence+=1
        try:
            before,after,usage=request(i)
            e={'request':i,'started_s':before-start,'finished_s':after-start,'latency_s':after-before,'input_tokens':usage['prompt_tokens'],'output_tokens':usage['completion_tokens']}
            with lock: events.append(e)
        except Exception as e:
            with lock: failures.append({'request':i,'elapsed_s':time.monotonic()-start,'error':str(e)})
            break
with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
    list(pool.map(lambda _:worker(),range(CONCURRENCY)))
elapsed=time.monotonic()-start
result={'label':LABEL,'started_at_unix':started_at,'duration_target_s':DURATION,'elapsed_s':elapsed,'concurrency':CONCURRENCY,'max_tokens':OUTPUT_TOKENS,'ignore_eos':True,'temperature':0,'model':'qwen3-0.6b','model_revision':'c1899de289a04d12100db370d81485cdf75e47ca','warmup_requests':2,'request_count':len(events),'errors':failures,'input_tokens':sum(e['input_tokens'] for e in events),'output_tokens':sum(e['output_tokens'] for e in events),'events':sorted(events,key=lambda e:e['finished_s'])}
result['input_tokens_per_second']=result['input_tokens']/elapsed
result['output_tokens_per_second']=result['output_tokens']/elapsed
print(json.dumps(result),flush=True)
if failures: raise SystemExit(1)
