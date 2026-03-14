import React from 'react';
import { render, type RenderOptions } from '@testing-library/react';
import { MemoryRouter, type MemoryRouterProps } from 'react-router-dom';
import userEvent from '@testing-library/user-event';

export { screen, waitFor, within, act } from '@testing-library/react';

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  routerProps?: MemoryRouterProps;
}

function Wrapper({ children, routerProps }: { children: React.ReactNode; routerProps?: MemoryRouterProps }) {
  return <MemoryRouter {...routerProps}>{children}</MemoryRouter>;
}

function customRender(ui: React.ReactElement, options: CustomRenderOptions = {}) {
  const { routerProps, ...renderOptions } = options;
  return {
    user: userEvent.setup(),
    ...render(ui, {
      wrapper: ({ children }) => <Wrapper routerProps={routerProps}>{children}</Wrapper>,
      ...renderOptions,
    }),
  };
}

export { customRender as render, userEvent };
