// SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
// SPDX-License-Identifier: MIT

package dawscript;

interface ValueListener
{
   long id();
   
   void onValue(Object value);
}
