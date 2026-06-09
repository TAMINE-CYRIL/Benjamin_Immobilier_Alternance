UPDATE annonce_enrichments
SET status = 'partial_success'
WHERE status = 'partial';
