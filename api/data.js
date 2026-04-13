export default async function handler(req, res) {
  const path = req.query.path || '';
  const vpsUrl = `http://194.163.136.244:8080/data/${path}`;
  
  try {
    const response = await fetch(vpsUrl);
    const data = await response.json();
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET');
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch from VPS' });
  }
}
