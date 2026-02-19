import SiteExtractionDebug from '@/components/debug/SiteExtractionDebug';

const DebugPage = () => {
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-2xl font-bold mb-6">Debug Tools</h1>
      <SiteExtractionDebug />
    </div>
  );
};

export default DebugPage;
