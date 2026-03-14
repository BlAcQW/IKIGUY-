import React, { useEffect, useState } from 'react';
import { listCalls, getCall } from '../lib/api';
import type { Call } from '../types';
import { PageHeader } from '@/components/PageHeader';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { PhoneCall, ChevronDown, ChevronUp, ChevronLeft, ChevronRight, ArrowUpDown, ArrowUp, ArrowDown, Search } from 'lucide-react';
import { toast } from 'sonner';

const statusVariant: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  IN_PROGRESS: 'default',
  ENDED: 'secondary',
  FAILED: 'destructive',
  QUEUED: 'outline',
  RINGING: 'outline',
};

type SortKey = 'type' | 'status' | 'duration' | 'createdAt';
type SortDir = 'asc' | 'desc';

export function CallsPage() {
  const [calls, setCalls] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [expandedData, setExpandedData] = useState<Call | null>(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('createdAt');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const limit = 20;

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const result = await listCalls(page, limit);
        setCalls(result.data);
        setTotal(result.meta?.total ?? 0);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        toast.error('Failed to load calls', { description: message });
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [page]);

  async function toggleExpand(id: string) {
    if (expandedId === id) {
      setExpandedId(null);
      setExpandedData(null);
      return;
    }
    try {
      const result = await getCall(id);
      setExpandedData(result.data);
      setExpandedId(id);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      toast.error('Failed to load call details', { description: message });
    }
  }

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir(key === 'createdAt' ? 'desc' : 'asc');
    }
  }

  const filtered = calls
    .filter((c) => {
      if (statusFilter !== 'all' && c.status !== statusFilter) return false;
      if (typeFilter !== 'all' && c.type !== typeFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        return c.id.toLowerCase().includes(q) || (c.phoneNumberId ?? '').toLowerCase().includes(q);
      }
      return true;
    })
    .sort((a, b) => {
      const dir = sortDir === 'asc' ? 1 : -1;
      switch (sortKey) {
        case 'type': return dir * a.type.localeCompare(b.type);
        case 'status': return dir * a.status.localeCompare(b.status);
        case 'duration': return dir * ((a.duration ?? 0) - (b.duration ?? 0));
        case 'createdAt': return dir * (new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime());
        default: return 0;
      }
    });

  const totalPages = Math.ceil(total / limit);

  function formatDuration(seconds: number | null): string {
    if (seconds === null) return '--';
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${String(s).padStart(2, '0')}`;
  }

  return (
    <div className="animate-slide-up">
      <PageHeader title="Call History" subtitle="View call history, transcripts, and recordings" />

      {loading ? (
        <Card>
          <div className="p-4 space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </Card>
      ) : calls.length === 0 && page === 1 ? (
        <Card className="border-dashed">
          <div className="py-16 text-center">
            <div className="w-14 h-14 rounded-2xl bg-muted/50 flex items-center justify-center mx-auto mb-4">
              <PhoneCall size={24} className="text-muted-foreground/40" />
            </div>
            <h2 className="text-base font-display font-semibold mb-1">No calls yet</h2>
            <p className="text-sm text-muted-foreground">Calls will appear here once you start making them.</p>
          </div>
        </Card>
      ) : (
        <>
          <div className="flex flex-wrap gap-3 mb-4">
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by ID or phone..."
                className="h-9 w-[220px] pl-9 text-xs"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px] h-9 text-xs">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="QUEUED">Queued</SelectItem>
                <SelectItem value="RINGING">Ringing</SelectItem>
                <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
                <SelectItem value="ENDED">Ended</SelectItem>
                <SelectItem value="FAILED">Failed</SelectItem>
              </SelectContent>
            </Select>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-[140px] h-9 text-xs">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="WEB">Web</SelectItem>
                <SelectItem value="INBOUND">Inbound</SelectItem>
                <SelectItem value="OUTBOUND">Outbound</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Card>
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="text-xs">ID</TableHead>
                  <TableHead className="text-xs cursor-pointer select-none" onClick={() => toggleSort('type')}>
                    <span className="inline-flex items-center gap-1">Type {sortKey === 'type' ? (sortDir === 'asc' ? <ArrowUp size={11} /> : <ArrowDown size={11} />) : <ArrowUpDown size={11} className="text-muted-foreground/40" />}</span>
                  </TableHead>
                  <TableHead className="text-xs cursor-pointer select-none" onClick={() => toggleSort('status')}>
                    <span className="inline-flex items-center gap-1">Status {sortKey === 'status' ? (sortDir === 'asc' ? <ArrowUp size={11} /> : <ArrowDown size={11} />) : <ArrowUpDown size={11} className="text-muted-foreground/40" />}</span>
                  </TableHead>
                  <TableHead className="text-xs cursor-pointer select-none" onClick={() => toggleSort('duration')}>
                    <span className="inline-flex items-center gap-1">Duration {sortKey === 'duration' ? (sortDir === 'asc' ? <ArrowUp size={11} /> : <ArrowDown size={11} />) : <ArrowUpDown size={11} className="text-muted-foreground/40" />}</span>
                  </TableHead>
                  <TableHead className="text-xs cursor-pointer select-none" onClick={() => toggleSort('createdAt')}>
                    <span className="inline-flex items-center gap-1">Created {sortKey === 'createdAt' ? (sortDir === 'asc' ? <ArrowUp size={11} /> : <ArrowDown size={11} />) : <ArrowUpDown size={11} className="text-muted-foreground/40" />}</span>
                  </TableHead>
                  <TableHead className="w-10"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((call) => (
                  <React.Fragment key={call.id}>
                    <TableRow className="cursor-pointer" onClick={() => toggleExpand(call.id)}>
                      <TableCell className="font-mono text-xs text-muted-foreground">{call.id.slice(0, 8)}...</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-[10px]">{call.type}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={statusVariant[call.status] ?? 'outline'} className="text-[10px]">
                          {call.status.replace('_', ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground">{formatDuration(call.duration)}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {new Date(call.createdAt).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        {expandedId === call.id ? (
                          <ChevronUp size={14} className="text-muted-foreground" />
                        ) : (
                          <ChevronDown size={14} className="text-muted-foreground" />
                        )}
                      </TableCell>
                    </TableRow>
                    {expandedId === call.id && expandedData && (
                      <TableRow className="hover:bg-transparent">
                        <TableCell colSpan={6} className="bg-muted/20 border-t-0">
                          <div className="grid grid-cols-2 gap-4 p-3 text-sm">
                            <div>
                              <span className="text-xs text-muted-foreground block mb-0.5">End Reason</span>
                              <span className="text-xs">{expandedData.endReason ?? '--'}</span>
                            </div>
                            <div>
                              <span className="text-xs text-muted-foreground block mb-0.5">Cost</span>
                              <span className="text-xs">{expandedData.cost != null ? `$${Number(expandedData.cost).toFixed(4)}` : '--'}</span>
                            </div>
                            {expandedData.recordingUrl && (
                              <div className="col-span-2">
                                <span className="text-xs text-muted-foreground block mb-0.5">Recording</span>
                                <a href={expandedData.recordingUrl} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline underline-offset-4">
                                  Listen
                                </a>
                              </div>
                            )}
                            {expandedData.transcript != null && (
                              <div className="col-span-2">
                                <span className="text-xs text-muted-foreground block mb-1.5">Transcript</span>
                                <div className="bg-background rounded-lg p-3 text-xs font-mono max-h-40 overflow-y-auto scrollbar-thin whitespace-pre-wrap border">
                                  {typeof expandedData.transcript === 'string'
                                    ? expandedData.transcript
                                    : JSON.stringify(expandedData.transcript as object, null, 2)}
                                </div>
                              </div>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </React.Fragment>
                ))}
              </TableBody>
            </Table>
          </Card>

          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-xs text-muted-foreground">
                Page {page} of {totalPages} ({total} total)
              </p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)} className="h-8 text-xs">
                  <ChevronLeft size={13} className="mr-1" /> Previous
                </Button>
                <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(page + 1)} className="h-8 text-xs">
                  Next <ChevronRight size={13} className="ml-1" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
