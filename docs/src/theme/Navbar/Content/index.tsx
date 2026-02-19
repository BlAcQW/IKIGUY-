import React from 'react';
import Content from '@theme-original/Navbar/Content';
import BrowserOnly from '@docusaurus/BrowserOnly';
import AuthNavbarItem from '../../../components/Auth/AuthNavbarItem';

export default function ContentWrapper(props) {
  return (
    <>
      <Content {...props} />
      <BrowserOnly>
        {() => <AuthNavbarItem />}
      </BrowserOnly>
    </>
  );
}
