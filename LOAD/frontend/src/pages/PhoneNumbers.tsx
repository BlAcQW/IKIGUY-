import React, { useEffect, useState, useCallback } from 'react';
import { listPhoneNumbers, searchPhoneNumbers, purchasePhoneNumber, createSipNumber, createGoipNumber, updatePhoneNumber, deletePhoneNumber, listAssistants } from '../lib/api';
import type { PhoneNumber, Assistant } from '../types';
import { PageHeader } from '@/components/PageHeader';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertDialog } from '@/components/ui/alert-dialog';
import { Phone, Plus, Trash2, Search, Globe, Radio } from 'lucide-react';
import { toast } from 'sonner';

interface SearchResult { number: string; locality: string; region: string; }
const NONE_VALUE = '__none__';

const COUNTRIES = [
  { code: 'US', name: 'United States' },
  { code: 'GB', name: 'United Kingdom' },
  { code: 'CA', name: 'Canada' },
  { code: 'AU', name: 'Australia' },
  { code: 'DE', name: 'Germany' },
  { code: 'FR', name: 'France' },
  { code: 'GH', name: 'Ghana' },
  { code: 'NG', name: 'Nigeria' },
  { code: 'ZA', name: 'South Africa' },
  { code: 'KE', name: 'Kenya' },
  { code: 'IN', name: 'India' },
  { code: 'BR', name: 'Brazil' },
  { code: 'MX', name: 'Mexico' },
  { code: 'JP', name: 'Japan' },
  { code: 'IL', name: 'Israel' },
  { code: 'SE', name: 'Sweden' },
  { code: 'NL', name: 'Netherlands' },
  { code: 'ES', name: 'Spain' },
  { code: 'IT', name: 'Italy' },
  { code: 'PH', name: 'Philippines' },
] as const;

export function PhoneNumbersPage() {
  const [numbers, setNumbers] = useState<PhoneNumber[]>([]);
  const [assistants, setAssistants] = useState<Assistant[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [searchCountry, setSearchCountry] = useState('US');
  const [searchAreaCode, setSearchAreaCode] = useState('');
  const [searchType, setSearchType] = useState<'local' | 'tollFree'>('local');
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [purchasing, setPurchasing] = useState<string | null>(null);
  const [sipNumber, setSipNumber] = useState('');
  const [sipName, setSipName] = useState('');
  const [sipDomain, setSipDomain] = useState('');
  const [creatingSip, setCreatingSip] = useState(false);
  const [goipNumber, setGoipNumber] = useState('');
  const [goipName, setGoipName] = useState('');
  const [goipTrunkName, setGoipTrunkName] = useState('');
  const [goipCountry, setGoipCountry] = useState('GH');
  const [creatingGoip, setCreatingGoip] = useState(false);
  const [releaseTarget, setReleaseTarget] = useState<{ id: string; number: string } | null>(null);
  const [releasing, setReleasing] = useState(false);

  const load = useCallback(async () => {
    try {
      const [numbersRes, assistantsRes] = await Promise.all([listPhoneNumbers(), listAssistants(1, 100)]);
      setNumbers(numbersRes.data); setAssistants(assistantsRes.data);
    } catch (err: unknown) { const msg = err instanceof Error ? err.message : 'Unknown error'; toast.error('Failed to load phone numbers', { description: msg }); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleSearch() {
    setSearching(true); setSearchResults([]);
    try {
      const result = await searchPhoneNumbers({ country: searchCountry, areaCode: searchAreaCode || undefined, type: searchType, limit: 10 });
      setSearchResults(result.data);
      if (result.data.length === 0) toast.info('No numbers found matching your criteria');
    } catch (err: unknown) { const msg = err instanceof Error ? err.message : 'Unknown error'; toast.error('Failed to search numbers', { description: msg }); }
    finally { setSearching(false); }
  }

  async function handlePurchase(number: string) {
    setPurchasing(number);
    try { await purchasePhoneNumber({ phoneNumber: number }); toast.success(`Purchased ${number}`); setDialogOpen(false); setSearchResults([]); await load(); }
    catch (err: unknown) { const msg = err instanceof Error ? err.message : 'Unknown error'; toast.error('Failed to purchase number', { description: msg }); }
    finally { setPurchasing(null); }
  }

  async function handleCreateSip(e: React.FormEvent) {
    e.preventDefault(); setCreatingSip(true);
    try {
      await createSipNumber({ number: sipNumber, name: sipName || undefined, provider: 'SIP_TRUNK', sipDomain: sipDomain || undefined });
      toast.success('SIP trunk number added'); setDialogOpen(false); setSipNumber(''); setSipName(''); setSipDomain(''); await load();
    } catch (err: unknown) { const msg = err instanceof Error ? err.message : 'Unknown error'; toast.error('Failed to add SIP number', { description: msg }); }
    finally { setCreatingSip(false); }
  }

  async function handleCreateGoip(e: React.FormEvent) {
    e.preventDefault(); setCreatingGoip(true);
    try {
      await createGoipNumber({ number: goipNumber, name: goipName || undefined, provider: 'GOIP', trunkName: goipTrunkName || undefined, country: goipCountry });
      toast.success('GoIP number added'); setDialogOpen(false); setGoipNumber(''); setGoipName(''); setGoipTrunkName(''); setGoipCountry('GH'); await load();
    } catch (err: unknown) { const msg = err instanceof Error ? err.message : 'Unknown error'; toast.error('Failed to add GoIP number', { description: msg }); }
    finally { setCreatingGoip(false); }
  }

  async function handleAssignAssistant(numberId: string, assistantId: string) {
    try { await updatePhoneNumber(numberId, { assistantId: assistantId === NONE_VALUE ? null : assistantId }); toast.success('Assistant assignment updated'); await load(); }
    catch (err: unknown) { const msg = err instanceof Error ? err.message : 'Unknown error'; toast.error('Failed to update assignment', { description: msg }); }
  }

  async function handleRelease() {
    if (!releaseTarget) return;
    setReleasing(true);
    try { await deletePhoneNumber(releaseTarget.id); toast.success(`Released ${releaseTarget.number}`); setReleaseTarget(null); await load(); }
    catch (err: unknown) { const msg = err instanceof Error ? err.message : 'Unknown error'; toast.error('Failed to release number', { description: msg }); }
    finally { setReleasing(false); }
  }

  return (
    <div className="animate-slide-up">
      <PageHeader title="Phone Numbers" subtitle="Manage your Twilio, SIP trunk, and GoIP phone numbers">
        <Button onClick={() => setDialogOpen(true)} className="font-semibold"><Plus size={15} className="mr-2" />Add Number</Button>
      </PageHeader>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-display">Add Phone Number</DialogTitle>
            <DialogDescription>Search for a number to purchase, add a SIP trunk, or register a GoIP GSM number.</DialogDescription>
          </DialogHeader>
          <Tabs defaultValue="search">
            <TabsList className="grid w-full grid-cols-3 h-9">
              <TabsTrigger value="search" className="text-xs gap-1.5"><Search size={12} />Search & Purchase</TabsTrigger>
              <TabsTrigger value="sip" className="text-xs gap-1.5"><Globe size={12} />SIP Trunk</TabsTrigger>
              <TabsTrigger value="goip" className="text-xs gap-1.5"><Radio size={12} />GoIP</TabsTrigger>
            </TabsList>
            <TabsContent value="search" className="space-y-4 mt-4">
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1"><Label className="text-[10px] uppercase tracking-wider text-muted-foreground">Country</Label>
                  <Select value={searchCountry} onValueChange={setSearchCountry}><SelectTrigger className="h-9"><SelectValue /></SelectTrigger><SelectContent>{COUNTRIES.map((c) => (<SelectItem key={c.code} value={c.code}>{c.code} — {c.name}</SelectItem>))}</SelectContent></Select>
                </div>
                <div className="space-y-1"><Label className="text-[10px] uppercase tracking-wider text-muted-foreground">Area Code</Label><Input value={searchAreaCode} onChange={(e) => setSearchAreaCode(e.target.value)} placeholder="415" className="h-9" /></div>
                <div className="space-y-1"><Label className="text-[10px] uppercase tracking-wider text-muted-foreground">Type</Label>
                  <Select value={searchType} onValueChange={(v) => setSearchType(v as 'local' | 'tollFree')}><SelectTrigger className="h-9"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="local">Local</SelectItem><SelectItem value="tollFree">Toll-Free</SelectItem></SelectContent></Select>
                </div>
              </div>
              <Button onClick={handleSearch} disabled={searching} className="w-full font-semibold">{searching ? 'Searching...' : 'Search Available Numbers'}</Button>
              {searchResults.length > 0 && (
                <div className="space-y-2 max-h-60 overflow-y-auto scrollbar-thin">
                  {searchResults.map((r) => (
                    <div key={r.number} className="flex items-center justify-between p-3 border rounded-lg hover:border-border/80 transition-colors">
                      <div><div className="font-mono text-sm">{r.number}</div><div className="text-[11px] text-muted-foreground">{r.locality}, {r.region}</div></div>
                      <Button size="sm" onClick={() => handlePurchase(r.number)} disabled={purchasing !== null} className="h-8 text-xs font-semibold">{purchasing === r.number ? 'Purchasing...' : 'Purchase'}</Button>
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>
            <TabsContent value="sip" className="mt-4">
              <form onSubmit={handleCreateSip} className="space-y-4">
                <div className="space-y-2"><Label className="text-xs font-medium">Phone Number (E.164)</Label><Input value={sipNumber} onChange={(e) => setSipNumber(e.target.value)} required placeholder="+14155551234" className="h-10" /></div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2"><Label className="text-xs font-medium">Name</Label><Input value={sipName} onChange={(e) => setSipName(e.target.value)} placeholder="Office Main Line" className="h-10" /></div>
                  <div className="space-y-2"><Label className="text-xs font-medium">SIP Domain</Label><Input value={sipDomain} onChange={(e) => setSipDomain(e.target.value)} placeholder="sip.example.com" className="h-10" /></div>
                </div>
                <DialogFooter><Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button><Button type="submit" disabled={creatingSip} className="font-semibold">{creatingSip ? 'Adding...' : 'Add SIP Number'}</Button></DialogFooter>
              </form>
            </TabsContent>
            <TabsContent value="goip" className="mt-4">
              <form onSubmit={handleCreateGoip} className="space-y-4">
                <p className="text-xs text-muted-foreground">Register a mobile number connected via GoIP (Hybertone) GSM gateway.</p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2"><Label className="text-xs font-medium">Country</Label>
                    <Select value={goipCountry} onValueChange={setGoipCountry}><SelectTrigger className="h-10"><SelectValue /></SelectTrigger><SelectContent>{COUNTRIES.map((c) => (<SelectItem key={c.code} value={c.code}>{c.code} — {c.name}</SelectItem>))}</SelectContent></Select>
                  </div>
                  <div className="space-y-2"><Label className="text-xs font-medium">Phone Number (E.164)</Label><Input value={goipNumber} onChange={(e) => setGoipNumber(e.target.value)} required placeholder="+233241234567" className="h-10" /></div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2"><Label className="text-xs font-medium">Name</Label><Input value={goipName} onChange={(e) => setGoipName(e.target.value)} placeholder="Ghana MTN Line 1" className="h-10" /></div>
                  <div className="space-y-2"><Label className="text-xs font-medium">Trunk Name</Label><Input value={goipTrunkName} onChange={(e) => setGoipTrunkName(e.target.value)} placeholder="goip-trunk" className="h-10" /></div>
                </div>
                <DialogFooter><Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button><Button type="submit" disabled={creatingGoip} className="font-semibold">{creatingGoip ? 'Adding...' : 'Add GoIP Number'}</Button></DialogFooter>
              </form>
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>

      <AlertDialog open={releaseTarget !== null} onOpenChange={(open) => !open && setReleaseTarget(null)} title="Release Phone Number" description={`Are you sure you want to release ${releaseTarget?.number ?? ''}? This cannot be undone.`} confirmLabel="Release" variant="destructive" loading={releasing} onConfirm={handleRelease} />

      {loading ? (
        <Card><CardContent className="p-0"><div className="p-4 space-y-3">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full" />)}</div></CardContent></Card>
      ) : numbers.length === 0 ? (
        <Card className="border-dashed"><CardContent className="py-16 text-center">
          <div className="w-14 h-14 rounded-2xl bg-muted/50 flex items-center justify-center mx-auto mb-4"><Phone size={24} className="text-muted-foreground/40" /></div>
          <h2 className="text-base font-display font-semibold mb-1">No phone numbers</h2>
          <p className="text-sm text-muted-foreground mb-5">Add a phone number to enable inbound and outbound calls.</p>
          <Button onClick={() => setDialogOpen(true)} className="font-semibold">Add Number</Button>
        </CardContent></Card>
      ) : (
        <Card><CardContent className="p-0">
          <Table>
            <TableHeader><TableRow className="hover:bg-transparent">
              <TableHead className="text-xs">Number</TableHead><TableHead className="text-xs">Name</TableHead><TableHead className="text-xs">Provider</TableHead>
              <TableHead className="text-xs">Status</TableHead><TableHead className="text-xs">Assigned Assistant</TableHead><TableHead className="w-[70px] text-xs">Actions</TableHead>
            </TableRow></TableHeader>
            <TableBody>
              {numbers.map((num) => (
                <TableRow key={num.id} className="group">
                  <TableCell className="font-mono text-sm">{num.number}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">{num.name ?? '--'}</TableCell>
                  <TableCell><Badge variant={num.provider === 'TWILIO' ? 'default' : num.provider === 'GOIP' ? 'outline' : 'secondary'} className={`text-[10px] ${num.provider === 'GOIP' ? 'border-emerald-500/50 text-emerald-600' : ''}`}>{num.provider}</Badge></TableCell>
                  <TableCell><Badge variant={num.status === 'ACTIVE' ? 'outline' : 'secondary'} className="text-[10px]">{num.status}</Badge></TableCell>
                  <TableCell>
                    <Select value={num.assistantId ?? NONE_VALUE} onValueChange={(v) => handleAssignAssistant(num.id, v)}>
                      <SelectTrigger className="h-8 w-[170px] text-xs"><SelectValue placeholder="None" /></SelectTrigger>
                      <SelectContent><SelectItem value={NONE_VALUE}>None</SelectItem>{assistants.map((a) => (<SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>))}</SelectContent>
                    </Select>
                  </TableCell>
                  <TableCell>
                    <Button variant="ghost" size="icon" onClick={() => setReleaseTarget({ id: num.id, number: num.number })} className="h-8 w-8 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity"><Trash2 size={13} /></Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent></Card>
      )}
    </div>
  );
}
