'use client'
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import styles from "../CSSModules/byuStyles.module.css";

declare module 'react' {
  namespace JSX {
    interface IntrinsicElements {
      "byu-header": React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement>;
      "byu-menu": React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & { slot?: string };
      "byu-user-info": React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & { slot?: string };
    }
  }
}

export default function BYUHeader() {

  return (
    <byu-header>
      <span slot="site-title">Chemistry Tutor</span>
      
      <byu-menu slot="nav">
        <Link to={'/'}>
        Home
        </Link>
        <Link to={'/classes'}>
        Classes
        </Link>
        <Link to={'/tools'}>
        Visual Tools
        </Link>
        <Link to={'/notes'}>
        Notes
        </Link>
        <Link to={'/math'}>
        Algebra Help
        </Link>

      </byu-menu>

      <byu-user-info slot="user">
        <a slot="login" href="/byu/login" className={styles.loginLink}>Sign In</a>
            <form
              slot="logout"
              method='POST'
              action='/byu/logout'
            >
              <input type='submit' value='Sign Out' className={styles.logoutLink}/>
            </form>
      </byu-user-info>
    </byu-header>
  );
}