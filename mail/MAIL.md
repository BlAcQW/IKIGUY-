  🔑 Account Credentials:

  noreply@ailabsafrica.com
  Password: noreply_secure_2025

  info@ailabsafrica.com
  Password: info_secure_2025

  🎯 Usage Ready:

  Both accounts are now production-ready and can be used in your applications:

  - noreply@ailabsafrica.com: For system notifications, password resets, automated emails
  - info@ailabsafrica.com: For customer inquiries, contact forms, general communication

  SMTP Settings for Applications:
  - Server: localhost or mail.inspirecreations.eu
  - Port: 587 (STARTTLS)
  - Authentication: Required
  - Security: STARTTLS/TLS




  

Here are the exact DNS records you need to add in Dynadot for each domain:

  1. For ailabsafrica.com (Add in Dynadot):

  Record Type: TXT
  Name: 2025._domainkey
  Value: v=DKIM1; h=sha256; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAveCY8O3rHyk7kMK6bdHiHHl/fkHQhYOr8+sRRWy3KR5MACDfhNH/Pf9BrfzfqcKHL3On21G
  IjNgEUvEgGkl/W2H/yKBQgzXnsRbQMjd1d7UBY0au3h7uQIB2fWMiu4KaMWyGLNkWduvBJkOMN/sBviOIlV8OXPpUjQ579B6FF9Er5e1rcoTC7TE9UZP1ZPYWrhLPKOFbFyEieovzHotBcXq2t1E66
  o06CW+n9LBz5yIquKQ8gzV70GofAduZRn9uPYT/CF6pywe6u4MZrI6ezn3Tht3CBEh75W6IPcUimH7z+TlOOWHWrcEArlEn5KBZCNveDFTNSxXVLjBQVrfJrwIDAQAB

  2. For inspirecreations.eu (Add in DNS provider):

  Record Type: TXT
  Name: 2025._domainkey
  Value: v=DKIM1; h=sha256; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwt3BzLGMG/SXVGzsHrpawRoMgvhl/reACNZEiap1JjwZZTfU8GxveNBrlVhumA5/ByU9xfF
  H3iJ2G0udrS2dhGfba8GO7MeSyJZuLSNmOpq4VvoNLVoLQcSz2l9ZsmWmZkKI5DgiAhivLnFSMz9r/vunP5DNj+X4wM8RMeZ7y7QkNxcIqk+UKuHo5sn0XNidFuTcclATOR+2heQFufnjLhKOerxQI
  hSr3Eh81xkNE2AdTczm4Ks+TesmIm/9n2yMBN26fsnVq/oNQK1WCKYkMjkMxSCNcvU/paG6cajD9hSKC62m6iI605Autk2qpAr36Mw2T/URNgkfRfUhe9O3NQIDAQAB

  3. For inspirecreations.it.com (Add in DNS provider):

  Record Type: TXT
  Name: 2025._domainkey
  Value: v=DKIM1; h=sha256; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAjzohcd0vsf936u554CbjqNj1gY/yz8ivFQk6Ub6vxxjik2k+xhfwMfZYv8HjQt1Wqmvjx6r
  eNt57eTIZZyIJQtbF6X6ntbZS++p1lnR1Ek83LFZJji8vK9chmROBEGn8OyeCB+QFD3vze5utvE4fYdCHyQmyQLFfQKy1h8722bXgfMxJihs1gMBgiho9KhkV9Mjl2ZndOEnh0AKKLYhrMmHi1dhAa
  9WYH8Wu4yxXlzJjwYWGPncJ6zgUrRk6Oaepn4qrdT08KlmNCoAXfcSJb5K6QY6+eVDDvFRv9024q39oQJf7yTWX9an7IFCCB93BoOKzmseKy/HvgfrDoYsFaQIDAQAB